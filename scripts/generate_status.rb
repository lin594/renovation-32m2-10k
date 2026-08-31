#!/usr/bin/env ruby
# frozen_string_literal: true

require "csv"
require "date"
require "yaml"

ROOT = File.expand_path("..", __dir__)
LEDGER_PATH = File.join(ROOT, "data", "ledger.csv")
OUTPUT_PATH = File.join(ROOT, "PROJECT_STATUS.md")

def money(value)
  format("¥%.2f", value)
end

ledger = CSV.read(LEDGER_PATH, headers: true)
budget = YAML.load_file(File.join(ROOT, "data", "budget.yaml"))
project = YAML.load_file(File.join(ROOT, "data", "project.yaml"))
procurement = YAML.load_file(File.join(ROOT, "data", "procurement.yaml"))
risks = YAML.load_file(File.join(ROOT, "data", "risks.yaml"))
schedule = YAML.load_file(File.join(ROOT, "data", "schedule.yaml"))

expenses = ledger.select { |row| row["flow"] == "expense" }.sum { |row| row["amount_cny"].to_f }
income = ledger.select { |row| row["flow"] == "income" }.sum { |row| row["amount_cny"].to_f }
net_outflow = expenses - income
undated_entries = ledger.count { |row| row["date"].to_s.empty? }

gate = budget.fetch("current_gate")
overall = budget.fetch("overall_budget_cny").to_f
trip = gate.fetch("october_trip_reserve_cny").to_f
paint = gate.fetch("paint_and_tools_plan_cny").to_f
contingency = gate.fetch("contingency_cny").to_f
reserved = trip + paint + contingency
available_conservative = overall - expenses - reserved
available_cash_view = overall - net_outflow - reserved

expense_by_category = ledger.select { |row| row["flow"] == "expense" }
  .group_by { |row| row["category"] }
  .transform_values { |rows| rows.sum { |row| row["amount_cny"].to_f } }
  .sort_by { |_category, amount| -amount }

phase_counts = Array(project["phases"]).group_by { |phase| phase["status"] }.transform_values(&:length)
task_counts = Array(project["active_tasks"]).group_by { |task| task["status"] }.transform_values(&:length)
buy_counts = Array(procurement["items"]).group_by { |item| item["status"] }.transform_values(&:length)
open_risks = Array(risks["risks"]).count { |risk| %w[open investigating].include?(risk["status"]) }
critical_open = Array(risks["risks"]).count do |risk|
  risk["severity"] == "critical" && %w[open investigating].include?(risk["status"])
end

updated_dates = [budget, project, procurement, risks, schedule].map do |document|
  value = document["updated"]
  Date.parse(value.to_s) if value
rescue Date::Error
  nil
end.compact
data_date = updated_dates.max&.iso8601 || "未登记"

category_rows = if expense_by_category.empty?
                  "| — | ¥0.00 |"
                else
                  expense_by_category.map { |category, amount| "| `#{category}` | #{money(amount)} |" }.join("\n")
                end

latest_rows = ledger.map { |row| row }.last(5).reverse.map do |row|
  sign = row["flow"] == "income" ? "+" : "−"
  date = row["date"].to_s.empty? ? "未登记" : row["date"]
  "| #{date} | `#{row['id']}` | #{row['item']} | #{sign}#{money(row['amount_cny'].to_f)} |"
end.join("\n")

content = <<~MARKDOWN
  <!-- 本文件由 scripts/generate_status.rb 自动生成，请修改 data/ 真源后运行 make status。 -->
  # 项目状态

  数据日期：#{data_date}。实际收支唯一真源：[data/ledger.csv](data/ledger.csv)。

  ## 资金快照

  | 指标 | 当前值 |
  |---|---:|
  | 总预算 | #{money(overall)} |
  | 累计支出 | #{money(expenses)} |
  | 累计收入 | #{money(income)} |
  | 净现金流出 | #{money(net_outflow)} |
  | 已规划预留（交通 + 涂装 + 应急） | #{money(reserved)} |
  | **其余工作可用上限（保守，不用收入冲抵）** | **#{money(available_conservative)}** |
  | 计入回收收入后的现金视角 | #{money(available_cash_view)} |

  保守公式：`#{money(overall)} − #{money(expenses)} − #{money(trip)}交通 − #{money(paint)}涂装 − #{money(contingency)}应急 = #{money(available_conservative)}`。

  这只是剩余上限，不代表尚未报价的防水、地面、马桶、防猫纱窗、门和基础用电已经买得下。

  数据质量提示：当前有 #{undated_entries} 笔历史账目未登记日期；金额汇总不受影响，但施工时间线仍不完整。

  ### 支出分类

  | 分类 | 累计支出 |
  |---|---:|
  #{category_rows}

  ### 最近五笔

  | 日期 | ID | 项目 | 现金变化 |
  |---|---|---|---:|
  #{latest_rows}

  ## 执行状态

  - 阶段：进行中 #{phase_counts.fetch('in_progress', 0)}，待开始 #{phase_counts.fetch('todo', 0)}，完成 #{phase_counts.fetch('done', 0)}。
  - 任务：进行中 #{task_counts.fetch('in_progress', 0)}，待办 #{task_counts.fetch('todo', 0)}，安全复核阻断 #{task_counts.fetch('blocked_by_safety_review', 0)}。
  - 采购：未购买 #{buy_counts.fetch('not_purchased', 0)}，待定制 #{buy_counts.fetch('pending_custom_order', 0)}，已到货 #{buy_counts.fetch('delivered', 0)}。
  - 开放风险：#{open_risks} 项，其中 critical #{critical_open} 项。开放风险不是已发生事故，而是尚未关闭的决策或验收门禁。

  ## 关键日期

  - 2026-09-30：远程备料与预约完成。
  - 2026-10-01～10-08：唯一双人主施工窗口。
  - 2026-10-08 后至 2027 年 1 月中旬：零装修专项往返。
  - 2027-01-15：三猫理想入住；2027-02-07：硬截止。

  ## 当前不应被误解的事项

  - 图纸是讨论方案，不是电气施工、燃气或防水验收证明。
  - 本户只有 L/N、无可用 PE；分级漏保降低风险但不等于接地。
  - 未报价必需项仍可能使 ¥10,000 目标不可行，采购继续受预算门禁约束。
MARKDOWN

File.write(OUTPUT_PATH, content)
puts "Generated #{OUTPUT_PATH.delete_prefix(ROOT + '/')}"
