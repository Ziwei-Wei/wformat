bool
Test()
{
    bool iDigitizerFlags = 0x01 | 0x02;

    return iDigitizerFlags & 0x01 &&
           iDigitizerFlags & (0x02 | 0x04);
}