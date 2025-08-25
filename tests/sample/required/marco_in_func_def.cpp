#define UNREF(x)

class TestClass
{

void 
TestUNREF(int UNREF(i));

void
Test(int i);

};

void 
TestClass::TestUNREF(int UNREF(i))
{
}

#define GSAL(_ANNOTATION_) _ANNOTATION_

inline void
write(GSAL(const int) buf, size_t bytes)
{
    (void)buf;
    (void)bytes;
}

int
main()
{
    write(GSAL(1), 0);
    return 0;
}