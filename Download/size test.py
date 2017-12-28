import os
print('length:',len(os.listdir('./')))
for i in os.listdir('./'):
    print(os.stat(i).st_size)