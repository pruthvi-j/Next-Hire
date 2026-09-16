"""
NEXT HIRE - Expected Answers & Key Concepts Seeder
Seeds the expected_answer and key_concepts fields for all 75 questions
from the dataset shown in the uploaded screenshots.

Run with:
    cd c:\\Users\\Admin\\Downloads\\NextHire\\backend
    python update_question_bank.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, execute_query, fetch_one

# ===================================================================
# COMPLETE DATASET: 75 Questions with Expected Answers & Key Concepts
# Source: NextHire Question Bank (uploaded dataset)
# ===================================================================

QUESTION_DATA = [
    # ---------------------------------------------------------------
    # PYTHON (PL001 - PL015)
    # ---------------------------------------------------------------
    {
        'code': 'PL001',
        'expected_answer': (
            "Python is a high-level, interpreted, general-purpose programming language. "
            "Its main features include simple syntax, dynamic typing, object-oriented "
            "programming, portability, and a large standard library."
        ),
        'key_concepts': "high-level, interpreted, general-purpose, simple syntax, dynamic typing, object-oriented, portability, standard library, Python"
    },
    {
        'code': 'PL002',
        'expected_answer': (
            "A variable is a name used to store or reference a value. "
            "Python variables do not require explicit type declaration."
        ),
        'key_concepts': "variable, name, store, reference, value, type declaration, Python"
    },
    {
        'code': 'PL003',
        'expected_answer': (
            "Common built-in types include int, float, complex, bool, str, list, tuple, set, dict, and NoneType."
        ),
        'key_concepts': "int, float, complex, bool, str, list, tuple, set, dict, NoneType, built-in types"
    },
    {
        'code': 'PL004',
        'expected_answer': (
            "= is the assignment operator used to assign a value to a variable. "
            "== is the comparison operator used to check whether two values are equal."
        ),
        'key_concepts': "assignment operator, comparison operator, equal, value, variable"
    },
    {
        'code': 'PL005',
        'expected_answer': (
            "if checks the first condition, elif checks additional conditions when previous conditions are false, "
            "and else executes when none of the conditions are true."
        ),
        'key_concepts': "if, elif, else, condition, conditions, false, true"
    },
    {
        'code': 'PL006',
        'expected_answer': (
            "A for loop is generally used to iterate over a sequence or iterable. "
            "A while loop repeats as long as its condition remains true."
        ),
        'key_concepts': "for loop, while loop, iterate, sequence, iterable, condition, repeats"
    },
    {
        'code': 'PL007',
        'expected_answer': (
            "A function is a reusable block of code that performs a specific task. "
            "It can accept parameters and return a value."
        ),
        'key_concepts': "function, reusable, block of code, specific task, parameters, return value"
    },
    {
        'code': 'PL008',
        'expected_answer': (
            "A list is mutable, meaning its elements can be changed. "
            "A tuple is immutable after creation. "
            "Lists use square brackets and tuples commonly use parentheses."
        ),
        'key_concepts': "mutable, immutable, list, tuple, elements, square brackets, parentheses"
    },
    {
        'code': 'PL009',
        'expected_answer': (
            "A dictionary stores data as key-value pairs. "
            "It is mutable and keys must be unique and hashable."
        ),
        'key_concepts': "dictionary, key-value pairs, mutable, keys, unique, hashable"
    },
    {
        'code': 'PL010',
        'expected_answer': (
            "Exception handling manages runtime errors without stopping the entire program. "
            "Code that may cause an exception is placed in try, and the except block handles the error."
        ),
        'key_concepts': "exception handling, runtime errors, try, except, error, program"
    },
    {
        'code': 'PL011',
        'expected_answer': (
            "A class is a blueprint for creating objects. "
            "An object is an instance of a class containing its own data and behavior."
        ),
        'key_concepts': "class, blueprint, object, instance, data, behavior"
    },
    {
        'code': 'PL012',
        'expected_answer': (
            "Inheritance allows a child class to acquire attributes and methods from a parent class. "
            "It supports code reuse and hierarchical relationships."
        ),
        'key_concepts': "inheritance, child class, parent class, attributes, methods, code reuse, hierarchical"
    },
    {
        'code': 'PL013',
        'expected_answer': (
            "Polymorphism means the same interface or method name can have different behavior "
            "depending on the object or implementation."
        ),
        'key_concepts': "polymorphism, same interface, method name, different behavior, object, implementation"
    },
    {
        'code': 'PL014',
        'expected_answer': (
            "*args allows a function to accept a variable number of positional arguments. "
            "**kwargs allows a variable number of keyword arguments."
        ),
        'key_concepts': "args, kwargs, variable number, positional arguments, keyword arguments, function"
    },
    {
        'code': 'PL015',
        'expected_answer': (
            "A shallow copy creates a new outer object but may share nested objects with the original. "
            "A deep copy recursively creates copies of nested objects as well."
        ),
        'key_concepts': "shallow copy, deep copy, outer object, nested objects, recursively, original"
    },

    # ---------------------------------------------------------------
    # JAVA (PL016 - PL030)
    # ---------------------------------------------------------------
    {
        'code': 'PL016',
        'expected_answer': (
            "Java is a high-level, object-oriented programming language designed to be portable "
            "through the Java Virtual Machine."
        ),
        'key_concepts': "Java, high-level, object-oriented, portable, Java Virtual Machine, JVM"
    },
    {
        'code': 'PL017',
        'expected_answer': (
            "Major features include object-oriented programming, platform independence, robustness, "
            "security, multithreading, portability, and automatic memory management."
        ),
        'key_concepts': "object-oriented, platform independence, robustness, security, multithreading, portability, automatic memory management"
    },
    {
        'code': 'PL018',
        'expected_answer': (
            "JVM stands for Java Virtual Machine. It executes Java bytecode and provides platform independence."
        ),
        'key_concepts': "JVM, Java Virtual Machine, bytecode, platform independence"
    },
    {
        'code': 'PL019',
        'expected_answer': (
            "JDK is used to develop Java applications. JRE provides the environment required to run Java applications. "
            "JVM executes Java bytecode."
        ),
        'key_concepts': "JDK, JRE, JVM, develop, environment, run, bytecode"
    },
    {
        'code': 'PL020',
        'expected_answer': (
            "Java has eight primitive types: byte, short, int, long, float, double, char, and boolean."
        ),
        'key_concepts': "primitive types, byte, short, int, long, float, double, char, boolean, eight"
    },
    {
        'code': 'PL021',
        'expected_answer': (
            "The if block executes when the condition is true. The else block executes when the condition is false."
        ),
        'key_concepts': "if, else, condition, true, false, block, executes"
    },
    {
        'code': 'PL022',
        'expected_answer': (
            "Java supports for, while, and do-while loops. It also supports the enhanced for loop "
            "for iterating over arrays and collections."
        ),
        'key_concepts': "for loop, while loop, do-while, enhanced for loop, iterating, arrays, collections"
    },
    {
        'code': 'PL023',
        'expected_answer': (
            "A class is a blueprint that defines properties and methods. "
            "An object is an instance of that class."
        ),
        'key_concepts': "class, blueprint, properties, methods, object, instance"
    },
    {
        'code': 'PL024',
        'expected_answer': (
            "Encapsulation is the process of combining data and methods inside a class and restricting direct "
            "access to data, commonly using private fields and public methods."
        ),
        'key_concepts': "encapsulation, combining data, methods, class, restricting access, private fields, public methods"
    },
    {
        'code': 'PL025',
        'expected_answer': (
            "Inheritance allows one class to acquire properties and methods of another class "
            "using mechanisms such as extends."
        ),
        'key_concepts': "inheritance, acquire, properties, methods, class, extends"
    },
    {
        'code': 'PL026',
        'expected_answer': (
            "Method overloading means having multiple methods with the same name but different "
            "parameter lists in the same class."
        ),
        'key_concepts': "method overloading, multiple methods, same name, different parameters, class"
    },
    {
        'code': 'PL027',
        'expected_answer': (
            "Method overriding occurs when a subclass provides its own implementation of a method "
            "inherited from its parent class."
        ),
        'key_concepts': "method overriding, subclass, own implementation, inherited, parent class"
    },
    {
        'code': 'PL028',
        'expected_answer': (
            "An interface defines a contract of methods that implementing classes must provide. "
            "It supports abstraction and multiple-type inheritance."
        ),
        'key_concepts': "interface, contract, methods, implementing classes, abstraction, multiple inheritance"
    },
    {
        'code': 'PL029',
        'expected_answer': (
            "Exception handling manages runtime errors using constructs such as try, catch, finally, throw, and throws."
        ),
        'key_concepts': "exception handling, runtime errors, try, catch, finally, throw, throws"
    },
    {
        'code': 'PL030',
        'expected_answer': (
            "ArrayList uses a dynamic array and generally provides faster random access. "
            "LinkedList uses linked nodes and can be more efficient for certain insertions and removals."
        ),
        'key_concepts': "ArrayList, LinkedList, dynamic array, random access, linked nodes, insertions, removals"
    },

    # ---------------------------------------------------------------
    # C (PL031 - PL045)
    # ---------------------------------------------------------------
    {
        'code': 'PL031',
        'expected_answer': (
            "C is a general-purpose procedural programming language widely used for system programming, "
            "embedded systems, and application development."
        ),
        'key_concepts': "C, general-purpose, procedural, system programming, embedded systems, application development"
    },
    {
        'code': 'PL032',
        'expected_answer': (
            "A variable is a named memory location used to store a value of a particular data type."
        ),
        'key_concepts': "variable, named memory location, store, value, data type"
    },
    {
        'code': 'PL033',
        'expected_answer': (
            "Common basic data types include char, int, float, and double. "
            "C also supports derived and user-defined types."
        ),
        'key_concepts': "char, int, float, double, derived types, user-defined types, data types"
    },
    {
        'code': 'PL034',
        'expected_answer': (
            "Arithmetic operators perform calculations such as +, -, *, /, and %. "
            "Relational operators compare values, such as ==, !=, <, >, <=, and >=."
        ),
        'key_concepts': "arithmetic operators, relational operators, calculations, compare, values"
    },
    {
        'code': 'PL035',
        'expected_answer': (
            "The if statement executes code when a condition is true. "
            "The else statement executes alternative code when the condition is false."
        ),
        'key_concepts': "if statement, else statement, condition, true, false, alternative code"
    },
    {
        'code': 'PL036',
        'expected_answer': (
            "A for loop is commonly used when initialization, condition, and update can be written together. "
            "A while loop repeats while a condition remains true."
        ),
        'key_concepts': "for loop, while loop, initialization, condition, update, repeats, true"
    },
    {
        'code': 'PL037',
        'expected_answer': (
            "A function is a reusable block of code designed to perform a specific task. "
            "It can accept parameters and return a value."
        ),
        'key_concepts': "function, reusable, block of code, specific task, parameters, return value"
    },
    {
        'code': 'PL038',
        'expected_answer': (
            "An array is a collection of elements of the same data type stored in contiguous memory locations."
        ),
        'key_concepts': "array, collection, same data type, contiguous memory locations, elements"
    },
    {
        'code': 'PL039',
        'expected_answer': (
            "A pointer is a variable that stores the memory address of another variable."
        ),
        'key_concepts': "pointer, variable, memory address, stores, another variable"
    },
    {
        'code': 'PL040',
        'expected_answer': (
            "A NULL pointer is a pointer that does not point to a valid object or memory location. "
            "It is commonly assigned NULL to indicate no valid target."
        ),
        'key_concepts': "NULL pointer, does not point, valid object, memory location, NULL, no valid target"
    },
    {
        'code': 'PL041',
        'expected_answer': (
            "A structure is a user-defined data type that groups variables of different data types under one name."
        ),
        'key_concepts': "structure, user-defined data type, groups variables, different data types, one name"
    },
    {
        'code': 'PL042',
        'expected_answer': (
            "Dynamic memory allocation allows memory to be allocated and released during program execution "
            "using functions such as malloc, calloc, realloc, and free."
        ),
        'key_concepts': "dynamic memory allocation, allocated, released, malloc, calloc, realloc, free, program execution"
    },
    {
        'code': 'PL043',
        'expected_answer': (
            "malloc() allocates a specified number of bytes without initializing them. "
            "calloc() allocates memory for multiple elements and initializes the allocated memory to zero."
        ),
        'key_concepts': "malloc, calloc, bytes, initializing, multiple elements, initializes to zero"
    },
    {
        'code': 'PL044',
        'expected_answer': (
            "Pointer arithmetic allows operations such as incrementing or decrementing pointers. "
            "The pointer moves according to the size of the data type it points to."
        ),
        'key_concepts': "pointer arithmetic, incrementing, decrementing, pointer, size of data type, moves"
    },
    {
        'code': 'PL045',
        'expected_answer': (
            "Storage classes define properties such as scope, lifetime, and linkage. "
            "Common storage classes include auto, register, static, and extern."
        ),
        'key_concepts': "storage classes, scope, lifetime, linkage, auto, register, static, extern"
    },

    # ---------------------------------------------------------------
    # JavaScript (PL046 - PL060)
    # ---------------------------------------------------------------
    {
        'code': 'PL046',
        'expected_answer': (
            "JavaScript is a high-level programming language commonly used to create interactive "
            "and dynamic web applications."
        ),
        'key_concepts': "JavaScript, high-level, programming language, interactive, dynamic, web applications"
    },
    {
        'code': 'PL047',
        'expected_answer': (
            "var has function scope, while let and const have block scope. "
            "let allows reassignment, while const does not allow reassignment of the binding."
        ),
        'key_concepts': "var, let, const, function scope, block scope, reassignment, binding"
    },
    {
        'code': 'PL048',
        'expected_answer': (
            "JavaScript has primitive types such as string, number, bigint, boolean, undefined, symbol, "
            "and null, along with objects."
        ),
        'key_concepts': "string, number, bigint, boolean, undefined, symbol, null, objects, primitive types"
    },
    {
        'code': 'PL049',
        'expected_answer': (
            "A function is a reusable block of code that performs a task and can accept parameters "
            "and return a value."
        ),
        'key_concepts': "function, reusable, block of code, task, parameters, return value"
    },
    {
        'code': 'PL050',
        'expected_answer': (
            "An array is an ordered collection used to store multiple values in a single variable."
        ),
        'key_concepts': "array, ordered collection, multiple values, single variable, store"
    },
    {
        'code': 'PL051',
        'expected_answer': (
            "An object is a collection of properties represented as key-value pairs and can also contain methods."
        ),
        'key_concepts': "object, collection, properties, key-value pairs, methods"
    },
    {
        'code': 'PL052',
        'expected_answer': (
            "DOM stands for Document Object Model. It represents an HTML document as a tree of objects "
            "that JavaScript can read and modify."
        ),
        'key_concepts': "DOM, Document Object Model, HTML document, tree, objects, read, modify"
    },
    {
        'code': 'PL053',
        'expected_answer': (
            "An arrow function is a shorter syntax for writing functions using =>. "
            "It also has lexical this behavior."
        ),
        'key_concepts': "arrow function, shorter syntax, =>, lexical this, behavior"
    },
    {
        'code': 'PL054',
        'expected_answer': (
            "A Promise represents the eventual completion or failure of an asynchronous operation "
            "and can be in pending, fulfilled, or rejected states."
        ),
        'key_concepts': "Promise, asynchronous operation, completion, failure, pending, fulfilled, rejected"
    },
    {
        'code': 'PL055',
        'expected_answer': (
            "async and await provide a simpler syntax for working with Promises and asynchronous operations."
        ),
        'key_concepts': "async, await, simpler syntax, Promises, asynchronous operations"
    },
    {
        'code': 'PL056',
        'expected_answer': (
            "Scope determines where variables can be accessed. JavaScript has global, function, block, "
            "and module-related scopes."
        ),
        'key_concepts': "scope, variables, accessed, global, function scope, block scope, module"
    },
    {
        'code': 'PL057',
        'expected_answer': (
            "A closure occurs when a function remembers and can access variables from its surrounding "
            "lexical scope even after that outer function has finished executing."
        ),
        'key_concepts': "closure, function, remembers, variables, lexical scope, outer function, finished executing"
    },
    {
        'code': 'PL058',
        'expected_answer': (
            "Event bubbling is the process where an event starts at the target element and propagates "
            "upward through its parent elements."
        ),
        'key_concepts': "event bubbling, event, target element, propagates, upward, parent elements"
    },
    {
        'code': 'PL059',
        'expected_answer': (
            "Important ES6 features include let, const, arrow functions, classes, template literals, "
            "destructuring, modules, Promises, and default parameters."
        ),
        'key_concepts': "ES6, let, const, arrow functions, classes, template literals, destructuring, modules, Promises, default parameters"
    },
    {
        'code': 'PL060',
        'expected_answer': (
            "JSON stands for JavaScript Object Notation. It is a lightweight text format commonly used "
            "to exchange structured data between applications and APIs."
        ),
        'key_concepts': "JSON, JavaScript Object Notation, lightweight text format, exchange, structured data, APIs"
    },

    # ---------------------------------------------------------------
    # SQL (PL061 - PL075)
    # ---------------------------------------------------------------
    {
        'code': 'PL061',
        'expected_answer': (
            "SQL stands for Structured Query Language. It is used to create, retrieve, modify, "
            "and manage data in relational databases."
        ),
        'key_concepts': "SQL, Structured Query Language, create, retrieve, modify, manage, relational databases"
    },
    {
        'code': 'PL062',
        'expected_answer': (
            "DDL defines or changes database structures using commands such as CREATE, ALTER, and DROP. "
            "DML manipulates data using commands such as INSERT, UPDATE, and DELETE."
        ),
        'key_concepts': "DDL, DML, CREATE, ALTER, DROP, INSERT, UPDATE, DELETE, database structures, data"
    },
    {
        'code': 'PL063',
        'expected_answer': (
            "The SELECT statement is used to retrieve data from a table, for example SELECT * FROM employees."
        ),
        'key_concepts': "SELECT, retrieve data, table, FROM, query, employees"
    },
    {
        'code': 'PL064',
        'expected_answer': (
            "WHERE filters rows based on a specified condition."
        ),
        'key_concepts': "WHERE, filters, rows, specified condition"
    },
    {
        'code': 'PL065',
        'expected_answer': (
            "ASC sorts data in ascending order, while DESC sorts data in descending order."
        ),
        'key_concepts': "ASC, DESC, ascending order, descending order, sorts"
    },
    {
        'code': 'PL066',
        'expected_answer': (
            "Aggregate functions perform calculations on multiple rows. "
            "Examples include COUNT(), SUM(), AVG(), MIN(), and MAX()."
        ),
        'key_concepts': "aggregate functions, calculations, multiple rows, COUNT, SUM, AVG, MIN, MAX"
    },
    {
        'code': 'PL067',
        'expected_answer': (
            "GROUP BY groups rows with the same values so aggregate functions can be applied to each group."
        ),
        'key_concepts': "GROUP BY, groups rows, same values, aggregate functions, each group"
    },
    {
        'code': 'PL068',
        'expected_answer': (
            "WHERE filters individual rows before grouping. HAVING filters groups after GROUP BY "
            "and is commonly used with aggregate functions."
        ),
        'key_concepts': "WHERE, HAVING, filters, rows, before grouping, after GROUP BY, aggregate functions"
    },
    {
        'code': 'PL069',
        'expected_answer': (
            "An INNER JOIN returns rows where matching values exist in both joined tables."
        ),
        'key_concepts': "INNER JOIN, rows, matching values, both tables"
    },
    {
        'code': 'PL070',
        'expected_answer': (
            "INNER JOIN returns only matching rows from both tables. "
            "LEFT JOIN returns all rows from the left table and matching rows from the right table, "
            "with NULL values when no match exists."
        ),
        'key_concepts': "INNER JOIN, LEFT JOIN, matching rows, left table, right table, NULL values, no match"
    },
    {
        'code': 'PL071',
        'expected_answer': (
            "A primary key uniquely identifies each row in a table. It must contain unique and non-NULL values."
        ),
        'key_concepts': "primary key, uniquely identifies, row, table, unique, non-NULL"
    },
    {
        'code': 'PL072',
        'expected_answer': (
            "A foreign key is a column or set of columns that references a key in another table "
            "and helps maintain referential integrity."
        ),
        'key_concepts': "foreign key, column, references, another table, referential integrity"
    },
    {
        'code': 'PL073',
        'expected_answer': (
            "Normalization organizes data into related tables to reduce redundancy and improve data consistency."
        ),
        'key_concepts': "normalization, organizes data, related tables, reduce redundancy, data consistency"
    },
    {
        'code': 'PL074',
        'expected_answer': (
            "A subquery is a query nested inside another SQL query. Its result can be used by the outer query."
        ),
        'key_concepts': "subquery, nested query, SQL query, result, outer query"
    },
    {
        'code': 'PL075',
        'expected_answer': (
            "ACID stands for Atomicity, Consistency, Isolation, and Durability. "
            "These properties help ensure reliable and consistent database transactions."
        ),
        'key_concepts': "ACID, Atomicity, Consistency, Isolation, Durability, database transactions, reliable"
    },
]


def update_expected_answers():
    """
    Safe, idempotent seeder that updates expected_answer and key_concepts
    for all 75 questions by question_code. Does NOT touch any other fields.
    """
    print("=" * 55)
    print("   NEXT HIRE - Expected Answers & Key Concepts Seeder")
    print("=" * 55)

    # Initialize DB (applies migrations if needed)
    init_db()

    updated = 0
    skipped = 0
    not_found = 0

    for item in QUESTION_DATA:
        code = item['code']
        expected = item['expected_answer']
        concepts = item['key_concepts']

        existing = fetch_one("SELECT id FROM questions WHERE question_code = %s", (code,))
        if existing:
            execute_query(
                "UPDATE questions SET expected_answer = %s, key_concepts = %s WHERE question_code = %s",
                (expected, concepts, code)
            )
            updated += 1
        else:
            print(f"  [WARNING] Question {code} not found in database — run import_questions.py first.")
            not_found += 1

    print(f"\n  Updated : {updated} questions with expected answers & key concepts")
    print(f"  Skipped : {skipped}")
    print(f"  Missing : {not_found} (run import_questions.py first if > 0)")
    print(f"\n  [DONE] All expected answers seeded successfully.")
    print("=" * 55)
    return updated


if __name__ == '__main__':
    update_expected_answers()
