from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine


DATABASE_URL = "postgresql://zlkhaimrgorqjg:bbc08f13a8e820b66b3cc0880a36a676ec82c2b56d947918b823effda0098a5d@ec2-35-169-43-5.compute-1.amazonaws.com:5432/de54sdj8s0j75h"
engine = create_engine(DATABASE_URL)

Base = declarative_base()

TEST_DATABASE_URL = "postgresql://inlcknegcwestr:4c0054720d60ec5b4685964a8a7c50bd7626b41c87870901d87a601efbfa6cd6@ec2-18-232-216-229.compute-1.amazonaws.com:5432/d64m445r9a6b0r"
test_engine = create_engine(TEST_DATABASE_URL)