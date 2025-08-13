from dataclasses import dataclass


@dataclass
class BiocoderData:
    instance_id: str
    filePath: str
    numLines: int
    lineStart: int
    lineEnd: int
    signature: str
    comment: str
    content: str
    repository: str
    promptSummaryOnly: str
    contextCode: str
    goldenCode: str
    test_case_id: str
    language: str

    def to_dict(self):
        return {
            'filePath': self.filePath,
            'numLines': self.numLines,
            'lineStart': self.lineStart,
            'lineEnd': self.lineEnd,
            'signature': self.signature,
            'comment': self.comment,
            'content': self.content,
            'repository': self.repository,
            'promptSummaryOnly': self.promptSummaryOnly,
            'contextCode': self.contextCode,
            'goldenCode': self.goldenCode,
            'test_case_id': self.test_case_id,
            'language': self.language,
        }
