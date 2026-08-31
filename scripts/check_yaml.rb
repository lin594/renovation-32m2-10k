#!/usr/bin/env ruby
# frozen_string_literal: true

require "csv"
require "set"
require "yaml"

ROOT = File.expand_path("..", __dir__)
YAML_PATHS = ([File.join(ROOT, "house.yaml")] + Dir[File.join(ROOT, "data", "*.yaml")]).sort.freeze

errors = []
documents = {}

YAML_PATHS.each do |path|
  begin
    document = YAML.load_file(path)
    unless document.is_a?(Hash)
      errors << "#{path.delete_prefix(ROOT + "/")} 的顶层必须是 mapping"
      next
    end
    documents[File.basename(path)] = document
  rescue Psych::SyntaxError => e
    errors << "#{path.delete_prefix(ROOT + "/")} 无法解析：#{e.message.lines.first.strip}"
  end
end

ledger_rows = CSV.read(File.join(ROOT, "data", "ledger.csv"), headers: true)
ledger_ids = ledger_rows.map { |row| row["id"] }.compact.to_set
inventory_ids = Array(documents.dig("inventory.yaml", "items")).map { |item| item["id"] }.compact.to_set
procurement_ids = Array(documents.dig("procurement.yaml", "items")).map { |item| item["id"] }.compact.to_set
risk_ids = Array(documents.dig("risks.yaml", "risks")).map { |risk| risk["id"] }.compact.to_set
project = documents.fetch("project.yaml", {})
task_ids = Array(project["active_tasks"]).map { |task| task["id"] }.compact.to_set
work_ids = Array(project["completed_work"]).map { |work| work["id"] }.compact.to_set

validate_unique_ids = lambda do |items, location|
  ids = Array(items).map { |item| item["id"] }.compact
  ids.group_by(&:itself).each do |id, matches|
    errors << "#{location} 出现重复 ID：#{id}" if matches.length > 1
  end
end

validate_enum = lambda do |items, field, allowed, location|
  Array(items).each do |item|
    value = item[field]
    errors << "#{location} #{item['id']} 的 #{field}=#{value.inspect} 不在允许值中" unless allowed.include?(value)
  end
end

validate_unique_ids.call(documents.dig("inventory.yaml", "items"), "inventory.yaml items")
validate_unique_ids.call(documents.dig("procurement.yaml", "items"), "procurement.yaml items")
validate_unique_ids.call(documents.dig("risks.yaml", "risks"), "risks.yaml risks")
validate_unique_ids.call(project["active_tasks"], "project.yaml active_tasks")
validate_unique_ids.call(project["completed_work"], "project.yaml completed_work")

risks_document = documents.fetch("risks.yaml", {})
validate_enum.call(risks_document["risks"], "severity", Array(risks_document["severity_order"]), "risks.yaml")
validate_enum.call(risks_document["risks"], "status", Array(risks_document["status_values"]), "risks.yaml")

procurement_document = documents.fetch("procurement.yaml", {})
validate_enum.call(procurement_document["items"], "status", Array(procurement_document["status_values"]), "procurement.yaml")
validate_enum.call(project["phases"], "status", Array(project["phase_status_values"]), "project.yaml phases")
validate_enum.call(project["active_tasks"], "status", Array(project["task_status_values"]), "project.yaml active_tasks")

targets = {
  "cost_ref" => ledger_ids,
  "cost_refs" => ledger_ids,
  "inventory_ref" => inventory_ids,
  "procurement_ref" => procurement_ids,
  "risk_ref" => risk_ids,
  "risk_refs" => risk_ids,
  "task_ref" => task_ids,
  "completed_work_ref" => work_ids
}.freeze

walk = lambda do |value, location|
  case value
  when Hash
    value.each do |key, child|
      if targets.key?(key)
        Array(child).each do |reference|
          errors << "#{location}.#{key} 引用了不存在的 ID：#{reference}" unless targets[key].include?(reference)
        end
      end
      walk.call(child, "#{location}.#{key}")
    end
  when Array
    value.each_with_index { |child, index| walk.call(child, "#{location}[#{index}]") }
  end
end

documents.each { |name, document| walk.call(document, name) }

# Project-specific invariants for the approved October/January execution baseline.
schedule = documents.fetch("schedule.yaml", {})
budget = documents.fetch("budget.yaml", {})
procurement = Array(documents.dig("procurement.yaml", "items"))
procurement_by_id = procurement.to_h { |item| [item["id"], item] }

ledger_expenses = ledger_rows.select { |row| row["flow"] == "expense" }.sum { |row| row["amount_cny"].to_f }
ledger_income = ledger_rows.select { |row| row["flow"] == "income" }.sum { |row| row["amount_cny"].to_f }
ledger_net = ledger_expenses - ledger_income

schedule_gate = schedule.fetch("budget_gate", {})
budget_gate = budget.fetch("current_gate", {})
expected_budget_values = {
  "overall_budget_cny" => 10_000,
  "actual_expenses_after_tile_cny" => ledger_expenses,
  "actual_income_cny" => ledger_income,
  "actual_net_outflow_cny" => ledger_net,
  "october_trip_reserve_cny" => 700,
  "paint_and_tools_plan_cny" => 2_012,
  "contingency_cny" => 700,
  "available_for_other_work_cny" => 4_728
}.freeze

expected_budget_values.each do |key, expected|
  actual = schedule_gate[key]
  errors << "schedule.yaml budget_gate.#{key} 应为 #{expected}，实际为 #{actual.inspect}" unless actual == expected
end

errors << "budget.yaml overall_budget_cny 应为10000" unless budget["overall_budget_cny"] == 10_000
errors << "budget.yaml contingency_cny 应为700" unless budget["contingency_cny"] == 700
{
  "actual_expenses_cny" => ledger_expenses,
  "actual_income_cny" => ledger_income,
  "actual_net_outflow_cny" => ledger_net,
  "october_trip_reserve_cny" => 700,
  "paint_and_tools_plan_cny" => 2_012,
  "contingency_cny" => 700,
  "available_for_other_work_cny" => 4_728
}.each do |key, expected|
  actual = budget_gate[key]
  errors << "budget.yaml current_gate.#{key} 应为 #{expected}，实际为 #{actual.inspect}" unless actual == expected
end

no_trip = schedule.dig("onsite_windows", "no_special_trip") || {}
errors << "10月8日后至1月中旬的装修专项往返必须为0" unless no_trip["planned_renovation_roundtrips"] == 0
errors << "零往返期不得安排代理施工" unless no_trip["proxy_construction_planned"] == false

october_window = schedule.dig("onsite_windows", "october_main") || {}
january_window = schedule.dig("onsite_windows", "january_closeout") || {}
errors << "10月主施工应为2人且主负责人在场" unless october_window["people"] == 2 && october_window["main_leader_present"] == true
errors << "1月收尾应为1人且主负责人不在场" unless january_window["people"] == 1 && january_window["main_leader_present"] == false

cat_gate = schedule.fetch("cat_move_in_gate", {})
errors << "三猫理想入住日应为2027-01-15" unless cat_gate["ideal_date"] == "2027-01-15"
errors << "三猫入住硬截止应为2027-02-07" unless cat_gate["hard_deadline"] == "2027-02-07"

primer = procurement_by_id["BUY-0013"] || {}
topcoat = procurement_by_id["BUY-0014"] || {}
tools = procurement_by_id["BUY-0015"] || {}
errors << "底漆采购基线应为3桶、447元" unless primer["planned_quantity"] == 3 && primer["planned_total_cny"] == 447
errors << "面漆采购基线应为5桶、1495元" unless topcoat["planned_quantity"] == 5 && topcoat["planned_total_cny"] == 1_495
errors << "刷漆工具采购基线应为1套、70元" unless tools["planned_quantity"] == 1 && tools["planned_total_cny"] == 70

# Electrical invariants: these are planning facts, not a substitute for professional approval.
electrical = documents.fetch("electrical.yaml", {})
circuits = Array(electrical.dig("provisional_five_circuit_allocation", "circuits"))
expected_circuits = Set["RCBO-01", "RCBO-02", "RCBO-03", "MCB-04", "MCB-05"]
actual_circuits = circuits.map { |circuit| circuit["id"] }.to_set
errors << "electrical.yaml 必须恰好包含3漏保+2空开的5个既定回路" unless circuits.length == 5 && actual_circuits == expected_circuits

junctions = Array(electrical["junction_boxes"])
active_junctions = junctions.select { |junction| junction["status"] == "active_planned" }
pct_42_count = active_junctions.count { |junction| junction["terminal"] == "PCT-42" }
pct_62_count = active_junctions.count { |junction| junction["terminal"] == "PCT-62" }
errors << "electrical.yaml 在用逻辑节点应为PCT-42×1、PCT-62×5" unless active_junctions.length == 6 && pct_42_count == 1 && pct_62_count == 5

outlets = electrical.fetch("outlet_groups", {})
outlet_sum = %w[bedroom kitchen living_room hall_a_shelf].sum { |key| outlets.dig(key, "count").to_i }
errors << "electrical.yaml 插座组数明细应合计14组" unless outlets["total_planned"] == 14 && outlet_sum == 14
errors << "electrical.yaml 卫生间本期不应新增普通插座" unless outlets.dig("bathroom", "general_socket_count") == 0

balcony = electrical.dig("confirmed_conditions", "balcony") || {}
errors << "electrical.yaml 阳台必须保持无穿线孔且永久供电延期" unless balcony["no_electrical_penetration"] == true && balcony["permanent_power"] == "deferred"

terminal_procurement = electrical.dig("terminal_policy", "procurement") || {}
errors << "electrical.yaml PCT采购逻辑数量应为1只PCT-42和6只PCT-62（含备用）" unless terminal_procurement["pct_42"] == 1 && terminal_procurement["pct_62_active"] == 5 && terminal_procurement["pct_62_spare"] == 1 && terminal_procurement["pct_62_total"] == 6
errors << "electrical.yaml 新建固定线路通电门禁必须保持blocked" unless electrical.dig("commissioning_gate", "status") == "blocked"

socket_wire = Array(electrical.dig("cable_plan", "buy_now")).find { |item| item["item"] == "BVVB 2×2.5mm²" } || {}
errors << "electrical.yaml BVVB 2×2.5mm²首卷应为50m" unless socket_wire["quantity_m"] == 50 && socket_wire["rolls"] == 1

# The remaining balance is not a feasibility claim until mandatory quotes exist.
budget_feasibility = budget.fetch("feasibility", {})
quote_items = Array(budget_feasibility["unpriced_essential_scope"])
validate_unique_ids.call(quote_items, "budget.yaml feasibility.unpriced_essential_scope")
errors << "budget.yaml 必须把预算可行性标为待必需项报价验证" unless budget_feasibility["status"] == "unproven_until_essential_quotes"
errors << "budget.yaml 必需项报价门禁应包含7类" unless quote_items.length == 7
errors << "schedule.yaml 应同步预算报价门禁状态" unless schedule_gate["feasibility_status"] == "unproven_until_essential_quotes"

# Waterproof and energization gates must remain explicit in the execution schedule.
schedule_text = schedule.to_s
errors << "schedule.yaml 必须包含不少于24h的铺砖前蓄水试验" unless schedule_text.include?("不少于24h蓄水") || schedule_text.include?("不少于24h的蓄水")
errors << "schedule.yaml 必须阻止专业检测前新建固定线路通电" unless schedule_text.include?("新建固定线路") && schedule_text.include?("不得通电")

unless errors.empty?
  errors.each { |error| warn "ERROR: #{error}" }
  exit 1
end

puts "OK: #{documents.length} 个 YAML 文件及跨文件引用校验通过"
