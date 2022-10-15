import asyncio


def sum(a,b):
    return a+b

def product(a,b):
    return a*b

# main async function 
async def main():
    a = int(input("Enter a number: "))
    b = int(input("Enter another number: "))

    print("Calculating sum...")
    await asyncio.sleep(5)
    print(a, "+", b, "=", sum(a,b))

    print("Calculating product...")
    await asyncio.sleep(5)
    print(a, "*", b, "=", product(a,b))


asyncio.run(main())