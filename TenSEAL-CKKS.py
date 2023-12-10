import tenseal as ts
import numpy as np
from PIL import Image
import sqlite3
import time

# 函数用于生成CKKS的上下文
def gencontext():
    # 定义CKKS方案，指定加密参数，如8192的多项式模度和coeff_mod_bit_sizes的系数模大小
    context = ts.context(ts.SCHEME_TYPE.CKKS, 8192, coeff_mod_bit_sizes=[22 ,21, 21, 21, 21, 21, 21, 21, 21, 21])
    context.global_scale = pow(2, 21)
    context.generate_galois_keys()
    return context

# 接收一个TenSEAL上下文和一个Numpy数组，加密后生成CKKS Vector
def encrypt(context, np_tensor):
    return ts.ckks_vector(context, np_tensor)

context = gencontext()

# 测试图像
search_image_number = int(input("请输入测试图片的序号（1-5）: "))
image_search_path = rf'C:\Users\gaoyy\Desktop\TenSEAL\测试图片\{search_image_number}.png'
image_search = Image.open(image_search_path)

# 将图像转换为 NumPy 数组
image_array_search = np.array(image_search).flatten() / 255
enc_search = encrypt(context, image_array_search)

# 连接到SQLite数据库（如果不存在则会创建）
conn = sqlite3.connect('encrypted_images_CKKS.db')

# 创建一个名为images的表来存储加密图像数据
conn.execute('''CREATE TABLE IF NOT EXISTS images (
                    id INTEGER PRIMARY KEY,
                    encrypted_data BLOB
                )''')

# 清空表中的所有数据
conn.execute('DELETE FROM images')

# 提交更改
conn.commit()

# 开始计时
time_use1 = 0

# 将加密数据写入数据库
for i in range(1, 6):
    image_path = r'C:\Users\gaoyy\Desktop\TenSEAL\测试图片\{}.png'.format(i)
    image = Image.open(image_path)
    image_array = np.array(image).flatten() / 255

    time_s = time.time()
    
    # 加密图像
    enc = encrypt(context, image_array)

    # 结束计时
    time_use1 = time_use1 + time.time() - time_s
    
    # 序列化 CKKS Vector
    serialized_enc = enc.serialize()

    # 将序列化的数据存储到数据库中
    conn.execute("INSERT INTO images (encrypted_data) VALUES (?)", (serialized_enc,))

    # 提交更改并关闭连接
    conn.commit()

# 从数据库中读取加密数据(判断是否加密成功)
cursor = conn.execute("SELECT encrypted_data FROM images")
i = 1

# 开始计时
time_use3 = 0

for row in cursor:
    serialized_enc_from_db = row[0]
    
    # 反序列化
    enc_from_db = ts.ckks_vector_from(context, serialized_enc_from_db)

    # 解密数据
    time_s = time.time()
    decrypted_data = enc_from_db.decrypt()
    
    time_use3 = time_use3 + time.time() - time_s
    
    # 后续代码不重要，这里主要是尝试能否恢复到原始图片模式

    # 转换为numpy数组
    decrypted_array = np.array(decrypted_data)

    # 转换为图片 64 * 64 的灰度图
    decrypted_image_array = (decrypted_array * 255).astype(np.uint8).reshape((64, 64))
    decrypted_image = Image.fromarray(decrypted_image_array)
        
    decrypted_image_path_from_file = r'C:\Users\gaoyy\Desktop\TenSEAL\解密图片\{}_decrypted_from_file.png'.format(i)
    i = i + 1
    decrypted_image.save(decrypted_image_path_from_file)
    
# 从数据库中读取加密数据
cursor = conn.execute("SELECT encrypted_data FROM images")
# 初始化最小均方误差值为正无穷大
min_mse_value = float('inf') 
i = 1
min_index = 1
time_use2 = 0
for row in cursor:
    serialized_enc_from_db = row[0]
    
    # 反序列化
    enc_from_db = ts.ckks_vector_from(context, serialized_enc_from_db)

    time_s = time.time()
    
    # 计算MSE
    sub_enc = enc_search - enc_from_db
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