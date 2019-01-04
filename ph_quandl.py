import quandl


def get_quandl_metadata():
    quandl.ApiConfig.api_key = "G4L36mzXzxcKR5c_vyFr"
    metadata = quandl.Dataset("EOD").data().meta
    print(metadata)
    return
