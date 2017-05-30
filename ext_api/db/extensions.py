import datetime
from uuid import uuid1
from ext_api.db.helper import inject_table
from ext_api.config import extensions_table_name

inject_extensions_table = inject_table(extensions_table_name)


@inject_extensions_table
def get_creation_date(table):
    return table.creation_date_time


@inject_extensions_table
def put_extension(table, User, GithubUrl, ProjectPath):
    table.put_item(Item={
        'Part': 0,  # always 0
        'ID': str(uuid1()),
        'User': User,
        'CreatedAt': datetime.datetime.utcnow().isoformat(),
        'GithubUrl': GithubUrl,
        'ProjectPath': ProjectPath
    })


if __name__ == '__main__':
    # Print out some data about the table.
    # This will cause a request to be made to DynamoDB and its attribute
    # values will be set based on the response.
    print(get_creation_date())
