from repository.parts_repository import PartRepository

if __name__ == '__main__':
    repo = PartRepository()
    # r = repo.create_part("ramka")
    r = repo.get_part("ramka")
    # r = repo.get_all_parts()
    print(r)
