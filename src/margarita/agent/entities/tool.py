from dataclasses import dataclass


@dataclass
class Param:
    """Describes a single parameter for a tool exposed to the LLM.

    Attributes:
        name: Parameter name.
        type: Expected parameter type annotation.
        default: Optional default value.
    """

    """One-line summary: Descriptor for a tool parameter.

    Purpose
    - Describe a single parameter accepted by a tool, including its name, type and whether it is required.

    Public API
    - name (str): The parameter name.
    - type (str): The parameter type annotation as a string.
    - required (bool): Whether the parameter is required. Defaults to True.

    Examples
    >>> Param(name='path', type='str', required=True)
    """
    name: str
    type: str
    required: bool = True


@dataclass
class Tool:
    """Represents a callable tool that the LLM may invoke.

    Attributes:
        name: Tool name visible to the LLM.
        params: List of Param objects describing the tool's parameters.
        return_type: The expected return type of the tool.
    """

    """Represents a callable tool available to agents.

    One-line summary: Metadata for a tool including its parameters and return types.

    Extended description:
        Used to register tools with the agent runtime so the LLM may invoke them.

    Attributes:
        name (str): Tool identifier.
        params (list[Param]): Ordered list of parameters the tool accepts.
        return_types (list[str]): Possible return type names as strings.
        description (str | None): Optional human-friendly description.

    Examples:
    >>> Tool(name='add', params=[Param('a','int'), Param('b','int')], return_types=['int'], description='Add numbers')
    """
    name: str
    params: list[Param]
    return_types: list[str]
    description: str | None = None
