; ADT definitions

(struct_item
    name: (type_identifier) @name.definition.class) @definition.class

(enum_item
    name: (type_identifier) @name.definition.class) @definition.class

(union_item
    name: (type_identifier) @name.definition.class) @definition.class

; type aliases

(type_item
    name: (type_identifier) @name.definition.class) @definition.class

; method definitions

(declaration_list
    (function_item
        name: (identifier) @name.definition.method)) @definition.method

; function definitions

(function_item
    name: (identifier) @name.definition.function) @definition.function

; trait definitions
(trait_item
    name: (type_identifier) @name.definition.interface) @definition.interface

; module definitions
(mod_item
    name: (identifier) @name.definition.module) @definition.module

; macro definitions

(macro_definition
    name: (identifier) @name.definition.macro) @definition.macro

; references

(call_expression
    function: (identifier) @name.reference.call) @reference.call

(call_expression
    function: (field_expression
        field: (field_identifier) @name.reference.call)) @reference.call

(macro_invocation
    macro: (identifier) @name.reference.call) @reference.call

; implementations

(impl_item
    trait: (type_identifier) @name.reference.implementation) @reference.implementation

(impl_item
    type: (type_identifier) @name.reference.implementation
    !trait) @reference.implementation
