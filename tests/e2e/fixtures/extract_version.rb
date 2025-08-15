#!/usr/bin/env ruby

# extract_version.rb - Parse strings of the form <name>-<SemVer>
# Handles edge cases where name can contain dashes

def extract_version(input_string)
  # Use regex to match SemVer pattern at the end
  # SemVer format: major.minor.patch (with optional pre-release and build metadata)
  match = input_string.match(/^(.+)-(\d+\.\d+\.\d+(?:-[a-zA-Z0-9\-\.]+)?(?:\+[a-zA-Z0-9\-\.]+)?)$/)

  if match
    name = match[1]
    semver = match[2]
    return { name: name, semver: semver }
  else
    return nil
  end
end

def print_extraction(input_string)
  result = extract_version(input_string)
  if result
    puts "Input: #{input_string}"
    puts "  Name: #{result[:name]}"
    puts "  SemVer: #{result[:semver]}"
    puts
  else
    puts "Input: #{input_string}"
    puts "  Error: Could not parse as name-semver format"
    puts
  end
end

# Test cases as specified in the issue
test_cases = [
  "proj-alpha-2.10.3",    # Edge case: name with dashes
  "rails-7.0.4",          # Simple case
  "react-dom-18.2.0",     # Edge case: name with dashes
  "vue-router-4.1.6",     # Edge case: name with dashes
  "this-is-a-name-1.2.3", # Edge case from issue description
]

puts "Ruby Version Extractor"
puts "====================="
puts

test_cases.each do |test_case|
  print_extraction(test_case)
end
