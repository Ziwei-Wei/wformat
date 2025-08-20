// Pattern source inspiration: helper_macros.h enum streaming + basix enum_flags macro shapes
#include <cstdint>
#include <type_traits>
#include <iostream>

#define DEFINE_FLAGS(E)                                                                                                       \
    inline E operator|(E a, E b)                                                                                              \
    {                                                                                                                         \
        return static_cast<E>(static_cast<std::underlying_type<E>::type>(a) | static_cast<std::underlying_type<E>::type>(b)); \
    }                                                                                                                         \
    inline E& operator|=(E& a, E b)                                                                                           \
    {                                                                                                                         \
        return a = a | b;                                                                                                     \
    }                                                                                                                         \
    inline E operator&(E a, E b)                                                                                              \
    {                                                                                                                         \
        return static_cast<E>(static_cast<std::underlying_type<E>::type>(a) & static_cast<std::underlying_type<E>::type>(b)); \
    }                                                                                                                         \
    inline E operator~(E a) { return static_cast<E>(~static_cast<std::underlying_type<E>::type>(a)); }

enum class Perm : uint32_t
{
    None  = 0,
    Read  = 1,
    Write = 2,
    Exec  = 4
};

DEFINE_FLAGS(Perm)

#define MULTI_LINE_INVOKE(OBJ, ACT) \
    do {                            \
        if ((OBJ) != nullptr)       \
        {                           \
            (OBJ)->ACT();           \
        }                           \
    }                               \
    while (0)

struct R
{
    void
    ping()
    {
        std::cout << "ping\n";
    }
};

int
main()
{
    Perm p = Perm::Read | Perm::Exec;

    if ((p& Perm::Exec) == Perm::Exec)
    {
        std::cout << "exec set\n";
    }

    R r;
    MULTI_LINE_INVOKE(
        &r,
        ping
        );
}