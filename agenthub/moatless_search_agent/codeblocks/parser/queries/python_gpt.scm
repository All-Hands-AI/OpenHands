(
  (decorated_definition
    (class_definition
      (identifier) @identifier
      (block) @no_children
    ) .
  ) @root
  .
  (comment) @child.first @child.last  @definition.class
)

(
  (decorated_definition
      (function_definition
        (identifier) @identifier
        (block) @no_children
      )
    .
  ) @root
  .
  (comment) @child.first @child.last @definition.function
)

(
  (function_definition
    (identifier) @identifier
    (block) @no_children
  ) @root @definition.function
  .
  (comment) @child.first @child.last
)
