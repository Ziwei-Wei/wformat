// Pattern source: SortLicensedProduct comparator style (decode.cpp)
#include <cstdlib>
#include <iostream>

struct Pair { int a; int b; };

int __cdecl PairCompare(const void* p1,const void* p2){
    const Pair* x = static_cast<const Pair*>(p1);
    const Pair* y = static_cast<const Pair*>(p2);
    if(x->a != y->a) return x->a - y->a;
    return y->b - x->b;
}

int main(){
    Pair arr[3]={{2,9},{1,5},{2,3}};
    std::qsort(arr,3,sizeof(Pair),PairCompare);
    for(auto &p:arr) std::cout<<'('<<p.a<<','<<p.b<<") ";
}