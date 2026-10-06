#!/usr/bin/env ruby
# frozen_string_literal: true

require "yaml"

ROOT = File.expand_path("..", __dir__)
PROJECT_PATH = File.join(ROOT, "data", "project.yaml")
OUTPUT_PATH = ENV.fetch("ACTIONS_OUTPUT", File.join(ROOT, "NEXT_ACTIONS.md"))

project = YAML.load_file(PROJECT_PATH)
actions = Array(project["next_actions"])
priority_order = Array(project["action_priority_values"])
priority_rank = priority_order.each_with_index.to_h

sections = [
  ["ready", "现在可推进"],
  ["blocked", "先解除阻塞"],
  ["waiting", "等待施工窗口"],
  ["deferred", "已明确延期"]
].freeze

domain_labels = {
  "plumbing" => "水路", "electrical" => "电气", "plumbing_electrical" => "水电",
  "pet_safety" => "防猫", "doors_windows" => "门窗", "floor_coating" => "地面涂层",
  "coating" => "涂装", "balcony_finish" => "阳台", "budget" => "账目"
}.freeze
room_labels = {
  "kitchen" => "厨房", "bathroom" => "卫生间", "whole_house" => "全屋",
  "kitchen_bathroom" => "厨卫", "living_bedroom" => "客厅/卧室", "balcony" => "阳台",
  "bedroom" => "卧室"
}.freeze

lines = [
  "# 下一步行动指南",
  "",
  "> 本页由 `data/project.yaml#next_actions` 生成。状态或优先级变化请修改真源后运行 `make actions`；不要直接编辑本页。",
  "",
  "本清单只表达当前行动顺序，不替代现场复尺、持证电工判断或产品说明。`blocked` 项必须先完成所列门禁。",
  ""
]

sections.each do |status, heading|
  selected = actions.select { |action| action["status"] == status }
  selected.sort_by! do |action|
    [priority_rank.fetch(action["priority"], priority_order.length), action["id"].to_s]
  end

  lines << "## #{heading}"
  lines << ""
  if selected.empty?
    lines << "暂无。"
    lines << ""
    next
  end

  selected.each do |action|
    label = [
      action["priority"],
      domain_labels.fetch(action["domain"], action["domain"]),
      room_labels.fetch(action["room"], action["room"])
    ].compact.join(" · ")
    lines << "### #{action['id']}｜#{action['action']}"
    lines << ""
    lines << "- 标签：#{label}"
    lines << "- 完成标准：#{action['completion_rule']}"
    evidence = Array(action["evidence_required"])
    lines << "- 验收证据：#{evidence.join('、')}" unless evidence.empty?
    lines << "- 当前阻塞：#{action['blocker']}" if action["blocker"]

    references = []
    references << action["task_ref"] if action["task_ref"]
    references.concat(Array(action["risk_refs"]))
    references << action["risk_ref"] if action["risk_ref"]
    references << action["procurement_ref"] if action["procurement_ref"]
    references.compact!
    references.uniq!
    lines << "- 关联编号：#{references.join('、')}" unless references.empty?
    lines << ""
  end
end

File.write(OUTPUT_PATH, lines.join("\n"), mode: "w", encoding: "UTF-8")
