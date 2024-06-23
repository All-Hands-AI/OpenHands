(value_declaration (function_declaration_left (lower_case_identifier) @name.definition.function)) @definition.function

(function_call_expr (value_expr (value_qid) @name.reference.function)) @reference.function
(exposed_value (lower_case_identifier) @name.reference.function)) @reference.function
(type_annotation ((lower_case_identifier) @name.reference.function) (colon)) @reference.function

(type_declaration ((upper_case_identifier) @name.definition.type) ) @definition.type

(type_ref (upper_case_qid (upper_case_identifier) @name.reference.type)) @reference.type
(exposed_type (upper_case_identifier) @name.reference.type)) @reference.type

(type_declaration (union_variant (upper_case_identifier) @name.definition.union)) @definition.union

(value_expr (upper_case_qid (upper_case_identifier) @name.reference.union)) @reference.union


(module_declaration
    (upper_case_qid (upper_case_identifier)) @name.definition.module
) @definition.module
