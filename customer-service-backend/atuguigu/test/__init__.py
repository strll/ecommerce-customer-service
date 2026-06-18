def simple_generator():
    print("1. 准备开始")
    yield "我是产出的资源"
    print("2. 结束并清理")

# 第一步：调用方法，但其实它一行代码都没执行！只是生成了一个“录像带”对象
gen = simple_generator()

# 第二步：第一次按下播放键（next）
result = next(gen)
print(result)
# 控制台输出: "1. 准备开始"
# result 的值变成了 "我是产出的资源"，此时函数在 yield 这行【暂停】了。

# 第三步：第二次按下播放键（next）
try:
    next(gen)
    # 控制台输出: "2. 结束并清理"
    # 然后因为没有更多的 yield 了，函数结束，Python 会抛出 StopIteration 异常。
except StopIteration:
    pass