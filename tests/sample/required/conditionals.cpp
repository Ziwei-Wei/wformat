// Pattern source: conditional #ifdef / #else sections
#include <iostream>

int main()
{
#ifdef _WIN32
std::cout<<"win\n";
#else
std::cout<<"other\n";
#endif
}