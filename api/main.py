from repository.parts_repository import PartRepository
import sys


if __name__ == '__main__':
    repo = PartRepository()
    # r = repo.create_part(sys.argv[1])
    # r = repo.get_part(sys.argv[1])
    r = repo.get_all_parts()
    print(r)
