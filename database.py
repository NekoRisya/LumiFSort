from luminadb import Database, model, BaseModel

memdb = Database(":memory:")


@model(memdb)
class FileInfo(BaseModel):
    """File information"""
    kind: str
    ftype: str
    size: int
    path: str
    parent_rel: str
    parent: str


@model(memdb)
class DirectoryFeatures(BaseModel):
    path: str
    file_count: int
    directory_count: int
    total_size: int
    kind_distribution: str


@model(memdb)
class Classification(BaseModel):
    path: str
    category: str
    confidence: float
    reason: str
