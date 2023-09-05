all:
	clang -emit-llvm -S config/io.c
	llc -march=x86-64 -filetype=obj config/io.ll -o config/io.o
	# python3 main.py tests/gencode-002.tpp
	llvm-link meu_modulo.ll config/io.ll -o meu_modulo.bc
	clang meu_modulo.bc -o meu_modulo.o
	./meu_modulo.o

clean:
	rm *.ll *.o *.bc