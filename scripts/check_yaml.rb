#!/usr/bin/env ruby
# frozen_string_literal: true

require "csv"
require "set"
require "yaml"

ROOT = File.expand_path("..", __dir__)
YAML_PATHS = ([File.join(ROOT, "house.yaml")] + Dir[File.join(ROOT, "data", "*.yaml")]).sort.freeze

errors = []
documents = {}

check_duplicate_mapping_keys = lambda do |node, location|
  case node
  when Psych::Nodes::Stream, Psych::Nodes::Document, Psych::Nodes::Sequence
    node.children.each_with_index do |child, index|
      check_duplicate_mapping_keys.call(child, "#{location}[#{index}]")
    end
  when Psych::Nodes::Mapping
    seen = {}
    node.children.each_slice(2) do |key_node, value_node|
      key = key_node.respond_to?(:value) ? key_node.value : key_node.to_s
      if seen.key?(key)
        errors << "#{location} 出现重复键 #{key.inspect}（约第#{key_node.start_line + 1}行）"
      else
        seen[key] = true
      end
      check_duplicate_mapping_keys.call(value_node, "#{location}.#{key}")
    end
  end
end

YAML_PATHS.each do |path|
  begin
    check_duplicate_mapping_keys.call(Psych.parse_file(path), File.basename(path))
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
inventory = Array(documents.dig("inventory.yaml", "items"))
inventory_ids = inventory.map { |item| item["id"] }.compact.to_set
inventory_by_id = inventory.to_h { |item| [item["id"], item] }
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

errors << "budget.yaml overall_budget_cny 应为10000" unless budget["overall_budget_cny"] == 10_000
errors << "budget.yaml contingency_cny 应为700" unless budget["contingency_cny"] == 700
{
  "october_trip_reserve_cny" => 700,
  "paint_and_tools_plan_cny" => 299,
  "contingency_cny" => 700
}.each do |key, expected|
  budget_actual = budget_gate[key]
  schedule_actual = schedule_gate[key]
  errors << "budget.yaml current_gate.#{key} 应为 #{expected}，实际为 #{budget_actual.inspect}" unless budget_actual == expected
  errors << "schedule.yaml budget_gate.#{key} 应与预算一致" unless schedule_actual == expected
end

snapshot_keys = %w[actual_expenses_cny actual_expenses_after_tile_cny actual_income_cny actual_net_outflow_cny available_for_other_work_cny formula]
snapshot_keys.each do |key|
  errors << "budget.yaml 不应手写易漂移快照 #{key}，由PROJECT_STATUS生成" if budget_gate.key?(key)
  errors << "schedule.yaml 不应手写易漂移快照 #{key}，由PROJECT_STATUS生成" if schedule_gate.key?(key)
end
errors << "预算实际支出必须只引用data/ledger.csv" unless budget["actuals_source"] == "data/ledger.csv" && schedule_gate["actuals_source"] == "data/ledger.csv"

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
errors << "底漆采购基线应为3桶" unless primer["planned_quantity"] == 3
errors << "面漆采购基线应为4桶" unless topcoat["planned_quantity"] == 4
errors << "刷漆工具采购基线应为1套" unless tools["planned_quantity"] == 1

# Electrical invariants: these are planning facts, not a substitute for professional approval.
electrical = documents.fetch("electrical.yaml", {})
circuits = Array(electrical.dig("provisional_five_circuit_allocation", "circuits"))
expected_circuits = Set["RCBO-01", "RCBO-02", "RCBO-03", "MCB-04", "MCB-05"]
actual_circuits = circuits.map { |circuit| circuit["id"] }.to_set
errors << "electrical.yaml 必须恰好包含3漏保+2空开的5个既定回路" unless circuits.length == 5 && actual_circuits == expected_circuits

branch_nodes = Array(electrical.dig("branch_nodes", "examples"))
errors << "electrical.yaml 应冻结9个主节点+4个局部子节点" unless electrical.dig("branch_nodes", "model") == "nine_main_plus_four_local_subnodes" && electrical.dig("branch_nodes", "main_count") == 9 && electrical.dig("branch_nodes", "local_subnode_count") == 4 && electrical.dig("branch_nodes", "total_distribution_points") == 13 && branch_nodes.length == 13
errors << "A1必须在MCB-04下分为空调与冰箱两支" unless branch_nodes.any? { |node| node["id"] == "A1" && Array(node["outputs"]).to_set == Set["客厅空调", "冰箱"] }
errors << "BATH1必须包含浴霸、镜柜和独立主灯三支" unless branch_nodes.any? { |node| node["id"] == "BATH1" && Array(node["outputs"]).to_set == Set["浴霸", "浴室柜/镜灯", "卫生间独立主灯/机械开关支路"] }

outlets = electrical.fetch("outlet_groups", {})
outlet_sum = %w[bedroom kitchen living_room hall_a_shelf].sum { |key| outlets.dig(key, "count").to_i }
errors << "electrical.yaml 插座组数明细应合计19组" unless outlets["total_planned"] == 19 && outlet_sum == 19
errors << "electrical.yaml 卫生间本期不应新增普通插座" unless outlets.dig("bathroom", "general_socket_count") == 0

sofa_robot = outlets.dig("living_room", "sofa_robot_branch") || {}
errors << "扫地机与沙发应共用RCBO-03分支路径但保留两个独立插座点" unless sofa_robot["id"] == "LR-SOFA-ROBOT" && sofa_robot["circuit"] == "RCBO-03" && sofa_robot.dig("lower_robot_socket", "supply") == "always_on" && sofa_robot.dig("lower_robot_socket", "smart_control") == "forbidden" && sofa_robot.dig("upper_sofa_socket", "smart_plug_optional") == true

balcony = electrical.dig("confirmed_conditions", "balcony") || {}
errors << "electrical.yaml 阳台必须保持无穿线孔且永久供电延期" unless balcony["no_electrical_penetration"] == true && balcony["permanent_power"] == "deferred"

terminal_procurement = electrical.dig("terminal_policy", "procurement") || {}
errors << "端子策略应明确PCT-42/62双极分配逻辑" unless electrical.dig("terminal_policy", "pct42_semantics").to_s.include?("1对L/N输入") && electrical.dig("terminal_policy", "pct62_semantics").to_s.include?("3对L/N输出") && terminal_procurement["status"].to_s.include?("dual_pole_topology")
errors << "固定布线T接方案必须明确拒绝汽车线束类穿刺夹" unless electrical.to_s.include?("汽车线束类廉价穿刺夹")
errors << "electrical.yaml 新建固定线路通电门禁必须保持blocked" unless electrical.dig("commissioning_gate", "status") == "blocked"

terminal_buy = procurement_by_id["BUY-0025"] || {}
errors << "BUY-0025应冻结PCT-42理论6只/PCT-62理论7只并各按10只装采购" unless terminal_buy.to_s.include?("理论6只") && terminal_buy.to_s.include?("理论7只") && terminal_buy.to_s.include?("10只") && terminal_buy["status"] == "not_purchased"

circuits_by_id = circuits.to_h { |circuit| [circuit["id"], circuit] }
errors << "MCB-05只能承载卫生间专用馈线" unless Array(circuits_by_id.dig("MCB-05", "scope")) == ["卫生间专用馈线"]
errors << "MCB-04应只承担客厅空调和冰箱" unless Array(circuits_by_id.dig("MCB-04", "scope")).to_set == Set["客厅已有空调", "客厅冰箱"]
errors << "RCBO-01应只保留卧室插座/空调/固定照明，吊扇已退出" unless Array(circuits_by_id.dig("RCBO-01", "scope")).to_set == Set["卧室普通插座", "卧室已有空调", "卧室固定照明"]
errors << "RCBO-02应把厨房照明并入厨房空间主干" unless Array(circuits_by_id.dig("RCBO-02", "scope")).to_set == Set["厨房插座", "厨房固定设备", "厨房固定照明"]
errors << "RCBO-03不得再承载客厅空调或冰箱" if Array(circuits_by_id.dig("RCBO-03", "scope")).any? { |x| x.include?("空调") || x.include?("冰箱") }

layered_devices = Array(electrical.dig("layered_residual_protection", "devices"))
device_ids = layered_devices.map { |device| device["id"] }.to_set
expected_devices = Set["SRCD-AC-LIV", "SRCD-FRIDGE", "BATH-RCD-05"]
errors << "分级漏保设备表应只保留MCB-04两端末端漏保和卫生间总RCD" unless device_ids == expected_devices
bath_rcd = layered_devices.find { |device| device["id"] == "BATH-RCD-05" } || {}
errors << "卫生间三个负载必须全部位于BATH-RCD-05下游" unless Array(bath_rcd["branches"]).to_set == Set["浴霸", "浴室柜/镜灯", "卫生间基础照明"]
errors << "MCB-04两个负载必须各自具有末端漏保" unless device_ids.include?("SRCD-AC-LIV") && device_ids.include?("SRCD-FRIDGE")
panel_snapshot = electrical.dig("confirmed_conditions", "panel_snapshot") || {}
panel_positions = Array(panel_snapshot["branch_positions"])
errors << "配电箱现场快照必须记录3×C40 RCBO + 2×C32 MCB" unless panel_positions.length == 5 && panel_positions.count { |x| x["existing"].to_s.include?("C40") } == 3 && panel_positions.count { |x| x["existing"].to_s.include?("C32") } == 2
errors << "前四个主箱支路应保留并由副保护盒承担C20过流保护；第五路允许原位2P≤30mA或门外RCD回退" unless panel_positions.first(4).all? { |x| x["target"].to_s.include?("保留") && x["target"].to_s.include?("C20") } && panel_positions[4]["target"].to_s.include?("C20")
errors << "BUY-0036应为主箱旁明装副保护盒方案" unless procurement_by_id.dig("BUY-0036", "item").to_s.include?("副保护盒") && procurement_by_id.dig("BUY-0036", "planned_quantity") == 1
errors << "BUY-0036必须锁定18模副箱和5只2P C20/6kA" unless procurement_by_id.dig("BUY-0036", "requirements").to_s.include?("18模数") && procurement_by_id.dig("BUY-0036", "requirements").to_s.include?("2P C20") && procurement_by_id.dig("BUY-0036", "requirements").to_s.include?("共5只")
errors << "原位更换C20断路器旧方案应取消" unless procurement_by_id.dig("BUY-0037", "status") == "cancelled"


electrical_text = electrical.to_s
errors << "智能墙壁开关必须使用零火版且不得控制通用插座" unless electrical_text.include?("零火双开") && electrical_text.include?("不属于通用插座")
errors << "两线制方案必须禁止N/PE短接和管道接地" unless electrical_text.include?("N/PE短接") && electrical_text.include?("水管") && electrical_text.include?("燃气管")

socket_wire = Array(electrical.dig("cable_plan", "buy_now")).find { |item| item["item"] == "BVVB 2×2.5mm²" } || {}
errors << "electrical.yaml BVVB 2×2.5mm²应按100m两卷采购" unless socket_wire["quantity_m"] == 100 && socket_wire["rolls"] == 2
six_mm_takeoff = electrical.dig("cable_plan", "six_mm_takeoff") || {}
errors << "6mm²单根导体应按净21.2m、计划25m、相线采购30m冻结" unless six_mm_takeoff.dig("totals", "net_m_per_conductor") == 21.2 && six_mm_takeoff.dig("totals", "planned_cut_m_per_conductor") == 25.0 && six_mm_takeoff.dig("totals", "purchase_l_m") == 30
bvvb_takeoff = electrical.dig("cable_plan", "bvvb_2x2_5_takeoff") || {}
errors << "BVVB 2×2.5mm²应按净63.5m、下料85m、采购100m冻结" unless bvvb_takeoff["net_total_m"] == 63.5 && bvvb_takeoff["planned_cut_total_m"] == 85.0 && bvvb_takeoff["purchase_m"] == 100
control_takeoff = electrical.dig("cable_plan", "control_return_takeoff") || {}
errors << "BV 1×2.5mm²单芯灯控回线应取消" unless control_takeoff["purchase_bv_1x2_5_m"] == 0 && control_takeoff["strategy"].to_s.include?("取消单独BV 1×2.5")
segment_takeoff = electrical.dig("cable_plan", "segment_takeoff") || {}
errors << "旧逐段下料表应退役并等待2026-09-30墙面放样重测" unless segment_takeoff["status"] == "superseded_by_2026_09_30_final_route_remeasure_required" && Array(segment_takeoff["canonical_main_nodes"]).length == 9 && Array(segment_takeoff["canonical_local_subnodes"]).length == 4
errors << "采购表应同步6mm²相线30m、计划下料25m" unless procurement_by_id.dig("BUY-0038", "planned_quantity_m") == 30 && procurement_by_id.dig("BUY-0038", "planned_cut_m") == 25
errors << "BV 1×2.5mm²旧采购项应取消" unless procurement_by_id.dig("BUY-0039", "status") == "cancelled" && procurement_by_id.dig("BUY-0039", "planned_quantity_m") == 0
device_takeoff = electrical.fetch("surface_device_takeoff", {})
errors << "末端材料应锁定15个普通插座点、1个卧室空调点和2个客厅漏保点" unless device_takeoff.dig("outlet_faceplates", "ordinary_points", "quantity") == 15 && device_takeoff.dig("outlet_faceplates", "bedroom_ac_dedicated", "quantity") == 1 && device_takeoff.dig("outlet_faceplates", "living_endpoint_rcd", "quantity") == 2
errors << "客厅和卧室必须各锁定一只JZ-N2零火双开" unless device_takeoff.dig("switch_faceplates", "jz_n2_zero_neutral_dual", "quantity") == 2 && device_takeoff.dig("switch_faceplates", "jz_n2_zero_neutral_dual", "returns_per_device") == 2
errors << "卧室床下灯必须另计10A二孔专用照明连接点" unless device_takeoff.dig("outlet_faceplates", "bedroom_underbed_light_controlled", "quantity") == 1 && device_takeoff.dig("outlet_faceplates", "bedroom_underbed_light_controlled", "type").to_s.include?("10A二孔")
errors << "BUY-0041应记录两只JZ-N2和99.8元计划总价" unless procurement_by_id.dig("BUY-0041", "planned_quantity") == 2 && procurement_by_id.dig("BUY-0041", "planned_total_cny") == 99.8
errors << "BUY-0024应同步BVVB净63.5m、下料85m、采购100m" unless procurement_by_id.dig("BUY-0024", "estimated_net_m") == 63.5 && procurement_by_id.dig("BUY-0024", "planned_cut_m") == 85 && procurement_by_id.dig("BUY-0024", "planned_quantity_m") == 100
errors << "PCT-42/PCT-62采购应各冻结10只" unless electrical.dig("cable_plan", "buy_now").to_s.include?("PCT-42二进四出") && electrical.dig("cable_plan", "buy_now").to_s.include?("PCT-62二进六出") && electrical.dig("cable_plan", "buy_now").to_s.include?("10")
errors << "采购表应包含插座、开关和六个基础灯具的末端材料包" unless procurement_by_id.dig("BUY-0040", "planned_bom").to_s.include?("普通插座面板") && procurement_by_id.dig("BUY-0040", "planned_bom").to_s.include?("餐区双头可调明装射灯") && procurement_by_id.dig("BUY-0040", "status") == "not_purchased"
errors << "照明线旧1.5mm²采购项应取消" unless procurement_by_id.dig("BUY-0023", "status") == "cancelled"
errors << "应新增冰箱漏保型插座采购项" unless procurement_by_id.dig("BUY-0035", "item").to_s.include?("冰箱漏保型插座")

house = documents.fetch("house.yaml", {})
main_feed = house.dig("electrical", "plan", "main_feed_proposal").to_s
errors << "house.yaml 蓝色6mm²余线只能保留与颜色标识一致的用途候选" unless main_feed.include?("中性导体") && !main_feed.include?("拟用")

blue_wire = inventory_by_id["INV-0001"] || {}
errors << "INV-0001只能保留与蓝色标识一致的用途候选" unless blue_wire["planned_use"].to_s.include?("中性导体") && !blue_wire["note"].to_s.include?("改色电工胶布")
robot = inventory_by_id["INV-0006"] || {}
errors << "INV-0006应同步沙发与书桌之间的固定停靠区域" unless robot["location"].to_s.include?("沙发与书桌之间")

mirror_cabinet = procurement_by_id["BUY-0005"] || {}
errors << "BUY-0005应明确智能除雾镜柜及其BATH-RCD-05下游电源" unless mirror_cabinet["item"].to_s.include?("智能除雾镜柜") && mirror_cabinet.to_s.include?("BATH-RCD-05")

sofa_bed = procurement_by_id["BUY-0006"] || {}
errors << "BUY-0006应同时承担沙发和临时客卧，并保留隐私帘候选" unless sofa_bed["item"].to_s.include?("沙发床") && sofa_bed["privacy_option"].to_s.include?("隐私帘")

dishwasher = inventory_by_id["INV-0013"] || {}
dishwasher_kit = procurement_by_id["BUY-0034"] || {}
errors << "现有洗碗机必须进入库存而非重复采购设备" unless dishwasher["condition"].to_s.start_with?("owned") && dishwasher["planned_use"].to_s.include?("不采购新机")
errors << "洗碗机连接包必须覆盖止水、排水和无PE标识，且不得默认叠加设备级漏保" unless dishwasher_kit.to_s.include?("独立") && dishwasher_kit.to_s.include?("排水") && dishwasher_kit.to_s.include?("本户无PE") && dishwasher_kit.to_s.include?("不再默认增加同灵敏度设备级漏保")
errors << "厨房插座应新增洗碗机三孔常电点并由RCBO-02统一保护" unless outlets.dig("kitchen", "count") == 4 && outlets.dig("kitchen", "dishwasher", "upstream") == "RCBO-02" && outlets.dig("kitchen", "dishwasher", "protection").to_s.include?("C20/30mA")

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
