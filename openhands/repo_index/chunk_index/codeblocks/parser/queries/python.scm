(module . (_) @child.first @definition.module) @root

(decorated_definition [
    (function_definition) @check_child
    (class_definition) @check_child
  ]
) @root

(class_definition
  (identifier) @identifier
  (comment) @child.first @definition.class
  .
  (block (_) @child.last .)
) @root

(class_definition
  (identifier) @identifier
  (argument_list
    (
      [
        (identifier) @reference.type
      ]
      (",")?
    )*
  )?
  (":")
  (block . (_) @child.first)
) @root @definition.class

(function_definition
  (identifier) @identifier
  (parameters
    ("(")
    (
      [
        (identifier)  @parameter.identifier
        (_
          (identifier) @parameter.identifier
          (":")
          (type
            [
              (identifier) @parameter.type
              (string) @parameter.type
            ]
          )
        )
      ]
      (",")?
    )*
    (")")
  )
  (
    ("->")
    (type
      [
        (identifier) @reference.identifier
        (subscript) @reference.identifier ; TODO: Extract identifiers
      ]
    )
  )?
  (":")
  .
  [
    (
      (comment) ? @child.first
      (block
        (_)
      )
    )
    (
      (block
        . (_) @child.first
      )
    )
  ]
) @root @definition.function

(comment) @root @definition.comment

(import_statement [
  (aliased_import
    (dotted_name) @reference.identifier
    (identifier) @identifier
  )
  (dotted_name) @reference.identifier @identifier
  ]
) @root @definition.import

(import_from_statement
  ("from")
  .
  (relative_import) @reference.module
  ("import")
  (dotted_name) @reference.identifier @identifier @reference.type
) @root @definition.import

(import_from_statement
  ("from")
  .
  (dotted_name) @reference.module
  ("import")
  (
    (dotted_name) @reference.identifier
    (",")*
  )*
) @root @definition.import

(future_import_statement) @root @definition.import
(import_from_statement) @root @definition.import

(assignment
  left: [
    (identifier) @identifier
    (attribute
      (identifier)
      (".")
      (identifier)
    ) @identifier @reference.dependency
    (attribute) @identifier
  ]
  (
    (":")
    (type
      [
        (identifier) @reference.identifier @reference.type
        (subscript .
          (identifier) @reference.identifier @reference.type
        )
      ]
    )
  )?
  right: [
    (identifier) @reference.identifier @reference.dependency
    (attribute) @reference.identifier @reference.dependency
    (_) @child.first
  ]?
) @root @definition.assignment

(call
  [
    (identifier) @reference.identifier
    (attribute) @reference.identifier
  ]
  (argument_list
    (
      [
        (identifier) @reference.identifier
        (attribute) @reference.identifier
        (keyword_argument
          (attribute) @reference.identifier
        )
      ]
      (",")?
    )*
  )
) @root @definition.call

(expression_statement
  . (string
      (string_start)
      (string_content)
      (string_end)
  ) @definition.comment
) @root

(expression_statement
  (_) @check_child
) @root

(return_statement
  ("return")
  (_) @child.first @definition.statement
) @root

(if_statement
  (":")
  (block . (_) @child.first)
) @root @definition.compound

(for_statement
  (":")
  (block . (_) @child.first)
) @root @definition.compound

(while_statement
  (":")
  (block . (_) @child.first)
) @root @definition.compound

(with_statement
  (":")
  (block . (_) @child.first)
) @root @definition.compound

(match_statement
  (":")
  (block . (_) @child.first)
) @root @definition.compound

(elif_clause
  (":")
  (block . (_) @child.first)
) @root @definition.dependent_clause

(else_clause
  (":")
  (block . (_) @child.first)
) @root @definition.dependent_clause

(except_clause
  (":")
  (block . (_) @child.first)
) @root @definition.dependent_clause

(finally_clause
  (":")
  (block . (_) @child.first)
) @root @definition.dependent_clause

(_
  (":")
  . (_) @child.first
  (block . (_)) @definition.statement
) @root

(_
  (block . (_) @child.first)
) @root @definition.statement
