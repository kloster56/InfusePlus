from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.metadata.schema_classes import TagPropertiesClass
mcp = MetadataChangeProposalWrapper(
    entityUrn='urn:li:tag:PII',
    aspect=TagPropertiesClass(name='PII', description='Personally Identifiable Information')
)
client._graph.emit(mcp)
