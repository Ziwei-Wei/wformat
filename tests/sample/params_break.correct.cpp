#include <utility>

int
One(
    int i
    );

int
One0(
    int i = 0
    );

int
Two(
    int i,
    int j
    );

namespace N
{

struct C
{};

class A
{
public:

    A() = default;

    A(
        int i
        );

    int
    One(
        int i
        );

    int
    Two(
        int i,
        int j
        );

    void
    N(
        const C& c
        );

    int
    One0(
        int i = 0
        ) noexcept;

    auto
    One1(
        int i = 0
        ) const -> decltype(auto);

    int
    Two0(
        int i,
        int j
        ) noexcept;

    auto
    Two1(
        int i,
        int j
        ) const -> decltype(auto);
};

int
N::A::One0(
    int i
    ) noexcept
{
}

auto
N::A::One1(
    int i
    ) const -> decltype(auto)
{
}

template <typename T>
void
h(
    T&&
    ) noexcept
{
}

template <typename T>
void
g1(
    T&& x
    ) noexcept(noexcept(h(std::forward<T>(x))));

template <typename T>
void
g2(
    T&& x,
    int y
    ) noexcept(noexcept((h(std::forward<T>(x)))));

template <typename T>
decltype(std::declval<T>())
d1(T a)
{
    return a;
}

template <typename T, typename U>
decltype(std::declval<T>() + std::declval<U>())
d2(
    T a,
    U b
    )
{
    return a + b;
}

void
main()
{
    A a;
    A* pa = &a;

    a.One0(1);

    pa->One(1);

    (&a)->One0(1);

    (*pa).One(1);

    (*(&a)).One(1);

    (&(*pa))->One(1);

    N::g1<int>(1);

    g2<int>(
        1,
        1
        );

    One0(0);

    if (
        One(1) > 0
        )
    {
        Two(
            1,
            2
            );
    }

    while (
        One(1) &&
        Two(
            1,
            2
            ) &&
        One0(0) > 0
        )
    {
    }

    One(
        One(1)
        );

    auto res = a.One(
        a.Two(
            1,
            2
            )
        );
}

} // namespace N

void
N::A::N(
    const N::C& c
    )
{
}