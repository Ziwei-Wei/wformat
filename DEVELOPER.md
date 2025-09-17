# Developer Doc

## Clear old wformat ahead of development

run ```pip uninstall wformat -y```

## Initialize dev environment

run ```cmake --build build --config Debug --target python_project_setup```

## Run Tests

run ```pytest```

## Iso test on uncrustify

run ```src\wformat\bin\uncrustify.exe -c src\wformat\data\uncrustify.cfg -f tests\sample\xxx.formatted.cpp```

## Iso test on clang-format

run ```src\wformat\bin\clang-format.exe -style=file:src\wformat\data\.clang-format tests\sample\xxx.formatted.cpp```
