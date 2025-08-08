import aiohttp
import asyncio
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Dict, Optional, Literal
import json
from dataclasses import asdict
import requests

from dotenv import load_dotenv
import os
# Note: @dataclass is a decorator that automatically adds special methods to a class, such as __init__, __repr__, and __eq__.
# Below is called a Data Model
load_dotenv()

@dataclass
class ELDDriver:
    driverID: int
    firstName: str
    lastName: str
    phoneNo: str
    truckNo: Optional[str] = None
    truckCount: Optional[int] = None

class ELDSync:
    # Task: Task to modify the 
    def __init__(self, eld_api_url: str,  eld_api_key: str) -> None:
        self.eld_api_url = eld_api_url
        self.eld_api_key = eld_api_key
        self.eld_headers = {
            'X-Api-Key': self.eld_api_key,
            'Content-Type': 'application/json'
        }
    
    def fetch_eld_drivers_sync(self):
        """Synchronous version for Streamlit compatibility"""
        try:
            response = requests.get(
                f"{self.eld_api_url}/api/v1/driver/eld/", 
                headers=self.eld_headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if not data:
                return []

            drivers = []
            for item in data.get("Data", []):
                if not item:
                    continue
                    
                driver = item.get("Driver", {}) or {}
                # Note: {} outside of get is useful if we have the response of Driver as None rather than Nothing or with some response
                vehicle = item.get("Vehicle", {}) or {}
                
                driver_id = driver.get("ID", "")
                first_name = driver.get("FirstName", "")
                last_name = driver.get("LastName", "")
                phone_no = driver.get("PhoneNo", "")
                truck = vehicle.get("DisplayID", "")

                drivers.append(ELDDriver(
                    driverID=driver_id,
                    firstName=first_name,
                    lastName=last_name,
                    phoneNo=phone_no,
                    truckNo=truck
                ))

            return drivers
        except Exception as e:
            print(f"Error fetching drivers: {e}")
            return []
    
    async def fetch_eld_drivers(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.eld_api_url}/api/v1/driver/eld/", headers=self.eld_headers) as response:
                data = await response.json()
                
                if not data:
                    return []

                drivers = []
                for item in data.get("Data", []):
                    if not item:
                        continue
                        
                    driver = item.get("Driver", {}) or {}
                    # Note: {} outside of get is useful if we have the response of Driver as None rather than Nothing or with some response
                    vehicle = item.get("Vehicle", {}) or {}
                    
                    driver_id = driver.get("ID", "")
                    first_name = driver.get("FirstName", "")
                    last_name = driver.get("LastName", "")
                    phone_no = driver.get("PhoneNo", "")
                    truck = vehicle.get("DisplayID", "")

                    drivers.append(ELDDriver(
                        driverID=driver_id,
                        firstName=first_name,
                        lastName=last_name,
                        phoneNo=phone_no,
                        truckNo=truck
                    ))

                return drivers 

    def find_vehicle_conflicts(self, drivers: List[ELDDriver]):
        # Algorithm to find the duplicated the drivers
        """
        Arg: Drivers list of dataclass
        Task
         - initially, output in json those same trucks
        """

        
        # approach: go through each driver and save in hashmap
        truck_map = {}

        for driver in drivers:
            
            if driver.truckNo:
                # append to truck map
                truck = driver.truckNo
                truck_map[truck] = 1 + truck_map.get(truck, 0)
        
        # Update each driver with their truck count
        for driver in drivers:
            if driver.truckNo:
                driver.truckCount = truck_map.get(driver.truckNo, 0)
        
        incorrect_assignments = []
        for driver in drivers:
            if driver.truckNo and driver.truckCount > 1:
                incorrect_assignments.append(ELDDriver(
                        driverID=driver.driverID,
                        firstName=driver.firstName,
                        lastName=driver.lastName,
                        phoneNo=driver.phoneNo,
                        truckNo=driver.truckNo,
                        truckCount=driver.truckCount
                ))
        
        return incorrect_assignments


        # Lets return those which are having truckCount more than 1

        
        # check all driver.truck against hashmap and attach the count.


async def main():
    config = {
        "eld_api_url": os.getenv("ELD_API_URL"),
        "eld_api_key": os.getenv("ELD_API_KEY")
    }

    sync = ELDSync(**config)
    drivers = await sync.fetch_eld_drivers()

    # Note: above output will be the list of dataclass but we need list of dictionary. so we will convert back now.
    # driver_dict = [asdict(driver) for driver in drivers]

    # with open("fetched_drivers_final.json", "w") as f:
    #     json.dump(driver_dict, f)

    incorrect_assignments = sync.find_vehicle_conflicts(drivers)
    wrong_assgnmt_driver_dict = [asdict(driver) for driver in incorrect_assignments]

    with open("fetched_drivers_final.json", "w") as f:
        json.dump(wrong_assgnmt_driver_dict, f)

    print(len(drivers))
    
    return






if __name__ == "__main__":
    asyncio.run(main())
    # main()


