import tenseal as ts
import numpy as np
import sqlite3
from PIL import Image
import time

# 加密函数：接受一张图像，使用BFV同态机密将其加密为一个密文向量
def encrypt_image(image):
    # 将加密的图像转换为Numpy数组
    img_array = np.array(image)
    # 展平图像数组
    flattened_img = img_array.flatten()
    # BFV同态加密的创建：使用TenSEAL中的BFV同态加密创建了一个密文向量c1，可以进行同态加法和同态乘法
    c1 = ts.bfv_vector(ctx, flattened_img)
    return c1
 
ctx=ts.context(ts.SCHEME_TYPE.BFV,poly_modulus_degree=4096,plain_modulus=1032193)    
sk=ctx.secret_key()

# 创建或连接到数据库文件
conn = sqlite3.connect('encrypted_images_BFV.db')
cursor = conn.cursor()

# 创建表来存储加密数据
cursor.execute('''CREATE TABLE IF NOT EXISTS EncryptedImages (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    EncryptedData TEXT
                )''')

# 清空表中的所有数据
conn.execute('DELETE FROM EncryptedImages')

# 开始计时
time_use1 = 0

# 加载并加密图像
for i in range(1, 6):
    image_path = r'C:\Users\gaoyy\Desktop\TenSEAL\测试图片\{}.png'.format(i)
    img = Image.open(image_path)
    time_s = time.time()
    encrypted_data = encrypt_image(img)
    # 结束计时
    time_use1 = time_use1 + time.time() - time_s
    # 将加密后的数据转换为bytes
    encrypted_data_bytes = encrypted_data.serialize()  # 转换为bytes
    cursor.execute('''INSERT INTO EncryptedImages (EncryptedData) VALUES (?)''', (sqlite3.Binary(encrypted_data_bytes),))
    conn.commit()

# 关闭数据库连接
conn.close()

# 测试图像
search_image_number = int(input("请输入测试图片的序号（1-5）: "))
image_path_search = rf'C:\Users\gaoyy\Desktop\TenSEAL\测试图片\{search_image_number}.png'
img_search = Image.open(image_path_search)
encrypted_data_search = encrypt_image(img_search)

# 连接到数据库
conn = sqlite3.connect('encrypted_images_BFV.db')
cursor = conn.cursor()

# 从数据库中检索存储的加密数据
cursor.execute('''SELECT EncryptedData FROM EncryptedImages''')
rows = cursor.fetchall()
# 开始计时
time_use3 = 0

for row in rows:
    # 从数据库中检索的加密数据
    encrypted_data_bytes = row[0]
    
    # 将存储的加密数据转换为 TenSEAL 密文对象
    encrypted_data = ts.bfv_vector_from(ctx, encrypted_data_bytes)

    time_s = time.time()
    
    decrypted_data = encrypted_data.decrypt()
    
    # 结束计时
    time_use3 = time_use3 + time.time() - time_s
    
    i += 1    

# 从数据库中检索存储的加密数据
cursor.execute('''SELECT EncryptedData FROM EncryptedImages''')
rows = cursor.fetchall()

# 遍历每个检索到的行
# 初始化最小均方误差值为正无穷大
min_mse_value = float('inf') 
i = 1
min_index = 1

# 开始计时
time_use2 = 0

for row in rows:
    # 从数据库中检索的加密数据
    encrypted_data_bytes = row[0]
    
    # 将存储的加密数据转换为 TenSEAL 密文对象
    encrypted_data = ts.bfv_vector_from(ctx, encrypted_data_bytes)

    time_s = time.time()
    
    # 计算MSE
    sub_enc = encrypted_data_search - encrypted_data
    mse_enc = sub_enc * sub_enc
    mse_value = mse_enc.decrypt()
    
    # 计算列表中每个元素的和
    total_sum = sum(mse_value)

    # 计算列表中每个元素的平均值
    average_value = total_sum / len(mse_value)
    
    # 比较均方误差值，更新最小值和索引
    if average_value < min_mse_value:
        min_mse_value = average_value
        min_index = i

    # 结束计时
    time_use2 = time_use2 + time.time() - time_s
    
    i += 1    
    
print("找到最佳匹配项：", min_index)

print("加密时间：", time_use1)
print("匹配时间", time_use2)
print("解密时间", time_use3)
    
# 关闭数据库连接
conn.close()

# 判断是否正确
if(min_mse_value < 0.001):
    print("判断正确")
else:
    print("判断失败")
    
