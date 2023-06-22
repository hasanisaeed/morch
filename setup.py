import setuptools

setuptools.setup(name="micro_orch",
                 version="0.1.0",
                 author="Saeed Hasani Borzadaran",
                 author_email="hassanisaeed19@gmail.com",
                 description="Python Microservice Orchestrator",
                 long_description_content_type="text/markdown",
                 url="https://github.com/hasanisaeed/micro-orch",
                 keywords='microservice, saga, patterns, microservice patterns, saga pattern',
                 packages=setuptools.find_packages('src'),
                 package_dir={'': 'src'},
                 python_requires='>=3.9',
                 project_urls={
                     "Bug Tracker": "https://github.com/hasanisaeed/micro-orch/issues/new",
                 },
                 classifiers=[
                     "Programming Language :: Python :: 3",
                     "License :: OSI Approved :: MIT License",
                     "Operating System :: OS Independent",
                 ],
                 ),
