(classlessPredicate
  name: (predicateName) @name.definition.function) @definition.function

(memberPredicate
  name: (predicateName) @name.definition.method) @definition.method

(aritylessPredicateExpr
  name: (literalId) @name.reference.call) @reference.call

(module
  name: (moduleName) @name.definition.module) @definition.module

(dataclass
  name: (className) @name.definition.class) @definition.class

(datatype
  name: (className) @name.definition.class) @definition.class

(datatypeBranch
  name: (className) @name.definition.class) @definition.class

(qualifiedRhs
  name: (predicateName) @name.reference.call) @reference.call

(typeExpr
  name: (className) @name.reference.type) @reference.type
