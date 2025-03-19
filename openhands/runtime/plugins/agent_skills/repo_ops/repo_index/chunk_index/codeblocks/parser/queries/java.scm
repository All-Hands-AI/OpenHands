(program . (_) @child.first @definition.module) @root

(class_declaration
  (identifier) @identifier
  (class_body
    ("{") @child.first
  )
) @root @definition.class

(annotation_type_declaration
  (identifier) @identifier
  (annotation_type_body
    ("{") @child.first
  )
) @root @definition.class

(enum_declaration
  (identifier) @identifier
  (enum_body
    ("{") @child.first
  )
) @root @definition.class

(interface_declaration
  (identifier) @identifier
  (interface_body
    ("{") @child.first
  )
) @root @definition.class

(record_declaration
  (identifier) @identifier
  (class_body
    ("{") @child.first
  )
) @root @definition.class

(method_declaration
  (identifier) @identifier
  (block
    ("{") @child.first
  )
) @root @definition.function

(constructor_declaration
  (identifier) @identifier
  (constructor_body
    ("{") @child.first
  )
)  @root @definition.constructor

(_
  (block
    . ("{") @child.first
  )
) @root @definition.statement

(line_comment) @root @definition.comment
(block_comment) @root @definition.comment

(import_declaration
  (scoped_identifier) @reference.identifier @identifier
) @root @definition.import @reference.imports
