#include <iostream>

constexpr bool
IsPow2(unsigned v, int c = 0)
{
    return v && !(v & (v - 1));
}

[[nodiscard]]
int
NextId()
{
    static int id = 0;
    return ++id;
}

int
main()
{
    std::cout << IsPow2(16) << ' ' << NextId() << ' ' << NextId() << '\n';
}