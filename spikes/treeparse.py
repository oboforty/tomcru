
def get_paths(my_dict, s, c = []):
  if not my_dict[s]:
     yield c+[s]
  else:
     for i in my_dict[s]:
       yield from get_paths(i, c+[s])
