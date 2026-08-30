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

ledger_ids = CSV.read(File.join(ROOT, "data", "ledger.csv"), headers: true).map { |row| row["id"] }.compact.to_set
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

unless errors.empty?
  errors.each { |error| warn "ERROR: #{error}" }
  exit 1
end

puts "OK: #{documents.length} 个 YAML 文件及跨文件引用校验通过"
