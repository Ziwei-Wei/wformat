#include <vector>
#include <iostream>

class IntIterator {
public:
    explicit IntIterator(std::vector<int> v): _v(std::move(v)), _it(_v.begin()) {}
    bool HasNext() const { return _it != _v.end(); }
    int Next() { return *_it++; }
private:
    std::vector<int> _v;
    std::vector<int>::iterator _it;
};

int main() {
    IntIterator it({
        1,
        2,
        3
    });
    while(it.HasNext()) std::cout<<it.Next()<<' ';
}