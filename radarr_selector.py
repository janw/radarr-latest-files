import pandas as pd
import numpy as np
from logzero import logger
from os import environ
from os.path import expanduser, expandvars, realpath
from requests import Session

user = environ["JWT_USERNAME"]
passwd = environ["JWT_PASSWORD"]
login_url = environ["JWT_LOGIN_URL"]
api_key = environ["RADARR_API_KEY"]
api_url = environ["RADARR_API_URL"]
size_limit = int(environ.get("SIZELIMIT", "1500"))
list_filename = environ.get("LIST_FILENAME", "filelist.txt")


def main():
    logger.info(f"Logging in at {login_url}")
    s = Session()
    r = s.post(login_url, data={"username": user, "password": passwd})
    r.raise_for_status()

    logger.info(f"Getting movies at {api_url}")
    r = s.get(api_url + "/movie?apikey=" + api_key, cookies={"jwt_token": r.text})
    r.raise_for_status()

    df = pd.DataFrame.from_dict(r.json()).set_index("title")
    all_movies = len(df)

    df = df[(~df["movieFile"].isna())]
    existing_movies = len(df)
    logger.info(f"Found {all_movies} movies, {existing_movies} of which exist on disk")

    df = df[["sizeOnDisk", "added", "folderName"]]
    df = df.sort_values("added", ascending=False)
    df["sizeCumSum"] = df["sizeOnDisk"].cumsum()
    df["sizeCumSumGb"] = df["sizeCumSum"] / 1024 ** 3
    total_size = max(df["sizeCumSumGb"])
    logger.info(f"Total size of files is {total_size:.1f} GB")

    df = df[df["sizeCumSumGb"] < size_limit]

    fitting_movies = len(df)
    if fitting_movies == existing_movies:
        logger.info(f"All existing movies fit within the {size_limit} GB size limit")
    else:
        logger.info(f"{len(df)} movies fit within the {size_limit} GB size limit")

    expanded_fn = realpath(expanduser(expandvars(list_filename)))
    np.savetxt(
        expanded_fn, sorted(df["folderName"].values), fmt="%s",
    )
    logger.info(f"Wrote directory list to {expanded_fn}")


if __name__ == "__main__":
    main()
