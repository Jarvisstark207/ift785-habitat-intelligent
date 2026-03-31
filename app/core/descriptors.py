"""
Descripteurs de validation - Itération 8 : Méta-programmation
TypedField  : vérifie le type et les contraintes (max_length, allowed)
RangedField : vérifie qu'une valeur numérique est dans un intervalle
Les descripteurs interceptent __get__ et __set__ pour valider à l'assignation.
"""


class TypedField:
    """
    Descripteur qui vérifie le type d'un attribut et des contraintes optionnelles.
    Lève TypeError si le type est incorrect, ValueError pour les contraintes.
    """

    def __init__(self, expected_type, max_length=None, allowed=None):
        self.expected_type = expected_type
        self.max_length = max_length
        self.allowed = allowed
        self._attr_name = None

    def __set_name__(self, owner, name):
        self._attr_name = f"_{name}_val"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self._attr_name, None)

    def __set__(self, obj, value):
        if not isinstance(value, self.expected_type):
            raise TypeError(
                f"Attendu {self.expected_type.__name__}, "
                f"reçu {type(value).__name__} : {value!r}"
            )
        if self.max_length is not None and hasattr(value, '__len__'):
            if len(value) > self.max_length:
                raise ValueError(
                    f"Longueur {len(value)} dépasse le maximum autorisé {self.max_length}"
                )
        if self.allowed is not None and value not in self.allowed:
            raise ValueError(
                f"Valeur {value!r} non autorisée. Valeurs acceptées : {self.allowed}"
            )
        setattr(obj, self._attr_name, value)

    def __delete__(self, obj):
        if hasattr(obj, self._attr_name):
            delattr(obj, self._attr_name)
