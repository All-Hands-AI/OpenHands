(class_definition
  name: (identifier) @name.class) @definition.class

(function_definition
  name: (identifier) @name.function) @definition.function

(class_definition
  name: (identifier) @name.class
  body: (_
    (function_definition
      name: (identifier) @name.method
      body: (block)) @definition.method))
