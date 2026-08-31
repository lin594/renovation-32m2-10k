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

unless errors.empty?
  errors.each { |error| warn "ERROR: #{error}" }
  exit 1
end

puts "OK: #{documents.length} 个 YAML 文件及跨文件引用校验通过"
