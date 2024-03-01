nodes=[{"bucket.id":"1234","bucket.project_number":"vbnhjhg","bucket.kind":"3456768765"}]
actual_nodes = {(n['bucket.id'], n['bucket.project_number'], n['bucket.kind']) for n in nodes}
print(actual_nodes)
