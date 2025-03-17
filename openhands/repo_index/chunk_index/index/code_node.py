from hashlib import sha256

from llama_index.core.schema import TextNode


class CodeNode(TextNode):
    # Skip start and end line in metadata to try to lower the number of changes and triggers of new embeddings.
    @property
    def hash(self):
        metadata = self.metadata.copy()
        metadata.pop('start_line', None)
        metadata.pop('end_line', None)
        doc_identity = str(self.text) + str(metadata)
        return str(sha256(doc_identity.encode('utf-8', 'surrogatepass')).hexdigest())
