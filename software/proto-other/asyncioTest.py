import asyncio

def larger(a,b):
    if a > b:
        return a
    else: 
        return b

def average(a,b):
    return (float) (a+b)/2

# main async function 
async def main():
    a = int(input("Enter a number: "))
    b = int(input("Enter another number: "))

    print("Calculating larger value...")
    await asyncio.sleep(2)
    print(larger(a,b), "is larger.")

    print("Calculating average...")
    await asyncio.sleep(5)
    print("The average of", a, "and", b, "is", average(a,b))

asyncio.run(main())