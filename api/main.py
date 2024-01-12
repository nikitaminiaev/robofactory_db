from repository.parts_repository import PartRepository

if __name__ == '__main__':
    repo = PartRepository()
    r = repo.get_row()
    print(r)
