import asyncio

async def coffee():
    print("Coffee START")
    await asyncio.sleep(3)        
    print("Coffee END")

async def toast():
    print("Toast START") 
    await asyncio.sleep(2)         
    print("Toast END")

async def main():
    
    await asyncio.gather(coffee(), toast())  #

asyncio.run(main())