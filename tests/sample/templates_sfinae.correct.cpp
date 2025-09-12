#include <type_traits>
#include <iostream>
#include <string>

template <class T, class = void>
struct Kind
{
    static constexpr const char*
    name()
    {
        return "other";
    }
};

template <class T>
struct Kind<T, std::enable_if_t<std::is_integral_v<T>>>
{
    static constexpr const char*
    name()
    {
        return "integral";
    }
};

template <class T>
auto
Describe(
    T v
    ) -> std::enable_if_t<std::is_integral_v<T>, std::string>
{
    return std::string(Kind<T>::name()) + ":" + std::to_string((long long) v);
}

int
main()
{
    std::cout << Describe(42) << '\n';
}