package queryshield.privacy

default decision := {
    "allowed": false,
    "actions": {},
    "reason": "policy_violation"
}

valid_action(a) if a == "allow"
valid_action(a) if a == "mask"
valid_action(a) if a == "remove"


# ---------- Column lookup ----------

allowed(c) if {
    c.table
    c.name in input.allowed_columns[c.table]
}

rule(c) := r if {
    r := input.privacy_rules[c.table][c.name]
}


# ---------- Physical columns ----------

violations contains {
    "type": "unauthorized_column",
    "column": c.name,
    "table": c.table
} if {
    some c in input.physical_columns
    not allowed(c)
}

violations contains {
    "type": "missing_privacy_rule",
    "column": c.name,
    "table": c.table
} if {
    some c in input.physical_columns
    allowed(c)
    not rule(c)
}

violations contains {
    "type": "invalid_action",
    "column": c.name,
    "table": c.table
} if {
    some c in input.physical_columns
    r := rule(c)
    not valid_action(r.action)
}


# ---------- Derived columns ----------

violations contains {
    "type": "unauthorized_derived_source",
    "column": output,
    "source_column": source.name,
    "table": source.table
} if {
    some output in input.derived_columns
    some source in input.derived_columns[output].source_columns
    not allowed(source)
}

violations contains {
    "type": "missing_derived_source_privacy_rule",
    "column": output,
    "source_column": source.name,
    "table": source.table
} if {
    some output in input.derived_columns
    some source in input.derived_columns[output].source_columns
    allowed(source)
    not rule(source)
}


# ---------- Output actions ----------

output_action(name) := "allow" if {
    input.derived_columns[name]
}

output_action(name) := r.action if {
    some c in input.physical_columns
    c.name == name
    r := rule(c)
}


# ---------- Final decision ----------

decision := {
    "allowed": true,
    "actions": {
        name: output_action(name) |
        some name in input.result_columns
    },
    "reason": "policy_applied"
} if {
    count(violations) == 0
}