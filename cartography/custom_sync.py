from cartography import cli
from cartography import sync
from cartography.intel import aws
from cartography.intel import create_indexes

def build_custom_sync():
    s = sync.Sync()
    s.add_stages([
        ('create-indexes', create_indexes.run),
        ('aws', aws.start_aws_ingestion),
    ])
    return s

def main(argv):
    return cli.CLI(build_custom_sync(), prog='cartography').main(argv)

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv[1:]))