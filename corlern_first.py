# 这是我的第一个注释
# 打印一个简单的问候语
print("你好,世界!")

# 打印一些基本的数学运算
print("1 + 1 =", 1 + 1)
print("2 * 3 =", 2 * 3)

# 打印一个字符串拼接的例子
name = "小明"
age = 18
print("我叫" + name + "，今年" + str(age) + "岁")

# 打印一个格式化字符串的例子
print(f"我叫{name}，明年我{age + 1}岁了")

# 打印一个多行字符串
print("""
这是第一行
这是第二行
这是第三行
""")

# 打印一个列表
fruits = ["苹果", "香蕉", "橙子"]
print("我最喜欢的水果是", fruits[0])

# 打印一个字典
person = {
    "name": "小明",
    "age": 18,
    "city": "北京"
}
print("我叫" + person["name"] + "，今年" + str(person["age"]) + "岁，住在" + person["city"])    

# 打印一个函数
def greet(name):
    print("你好, " + name + "!")

greet("小明")

