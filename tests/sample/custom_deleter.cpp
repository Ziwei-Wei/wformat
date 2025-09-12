#include <cstdio>
#include <memory>
#include <iostream>

struct FileCloser {
    void operator()(std::FILE* f) const noexcept { if(f) std::fclose(f); }
};

int main(){
    std::unique_ptr<std::FILE,FileCloser> f(std::fopen("tmp_out.txt","w"));
    if(f) std::fputs("data\n", f.get());
    std::cout << "ok\n";
}